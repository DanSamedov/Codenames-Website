import json
import time
import threading
from dataclasses import dataclass, field
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from room.models import Player, Game
from game.models import Card
from game.utils.hints_logic import add_hint
from django.core.cache import cache
from django.db import transaction


class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['id']
        self.game_group_name = f'game_{self.game_id}'
        self.username = self.scope["session"].get("username")

        async_to_sync(self.channel_layer.group_add)(
            self.game_group_name,
            self.channel_name
        )
        self.accept()

        self.event_dispatcher = GameEventDispatcher(self.channel_layer, self.game_group_name, self.send)
        self.event_processor = GameEventProcessor(self.game_id)
        self.phase_manager = PhaseManager(self.game_id, self.channel_layer, self.game_group_name, self.event_dispatcher, self.event_processor)

        self.event_dispatcher.new_player(self.game_id)

        phase = self.phase_manager.get_phase()
        creator_username = Player.objects.get(game=self.game_id, creator=True).username

        if not phase and self.username == creator_username:
            self.phase_manager.set_phase("hint_phase_start", 10)
            self.phase_manager.start_phase_cycle()
        elif phase:
            self.phase_manager.handle_existing_phase()
            self.event_dispatcher.sync(phase)

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.game_group_name,
            self.channel_name
        )

    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        username = self.scope["session"].get("username")

        if not username:
            self.send(text_data=json.dumps({"error": "User not authenticated or no team assigned"}))
            return

        phase = self.phase_manager.get_phase()
        phase_name = phase.name

        if not phase:
            self.send(text_data=json.dumps({"error": "No game phase found"}))
            return

        action = data.get("action")
        
        if action == "card_choice" and phase_name == "round_phase_start":
            self.event_dispatcher.card_choice(
                username, 
                card_id=data.get("card_id"), 
                card_status=data.get("card_status")
            )
        elif action == "hint_submit" and phase_name == "hint_phase_start":
            self.event_dispatcher.hint_receive(data["hintWord"], data["hintNum"])
            self.event_processor.capture_hint(data)
            self.phase_manager.advance_phase()
        elif action == "picked_words":
            self.event_processor.capture_picks(data)

    def player_join(self, event):
        self.event_dispatcher.player_join(event)

    def choose_card(self, event):
        self.event_dispatcher.choose_card(event)

    def hint_display(self, event):
        self.event_dispatcher.hint_display(event)

    def sync_time(self, event):
        self.event_dispatcher.sync_time(event)

    def phase_event(self, event):
        self.event_dispatcher.phase_event(event)

    def reveal_cards(self, event):
        self.event_dispatcher.reveal_cards(event)

    def game_over(self, event):
        self.event_dispatcher.game_over(event)

@dataclass
class Phase:
    name: str
    duration: int
    start_time: float = field(default_factory=time.time)
    _transition_thread: threading.Thread = None

    def time_remaining(self) -> float:
        return max(0, (self.start_time + self.duration) - time.time())

    def schedule_transition(self, callback: callable) -> None:
        def transition_task():
            remaining = self.time_remaining()
            if remaining > 0:
                time.sleep(remaining)
            callback(self)

        if self._transition_thread is not None and self._transition_thread.is_alive():
            return
            
        self._transition_thread = threading.Thread(target=transition_task, daemon=True)
        self._transition_thread.start()

    def serialize(self) -> dict:
        return {
            "phase": self.name,
            "duration": self.duration,
            "start_time": self.start_time,
        }

class PhaseManager:
    def __init__(self, game_id, channel_layer, game_group_name, event_dispatcher, event_processor):
        self.game_id = game_id
        self.cache_prefix = f"game_{self.game_id}"
        self.channel_layer = channel_layer
        self.game_group_name = game_group_name
        self.event_dispatcher = event_dispatcher
        self.event_processor = event_processor
        self.current_phase = None

    def set_phase(self, phase_name, duration):
        self.current_phase = Phase(name=phase_name, duration=duration)
        cache.set(
            f"{self.cache_prefix}_phase",
            self.current_phase.serialize(),
            timeout=duration + 5
        )
        return self.current_phase

    def get_phase(self) -> Phase:
        phase_data = cache.get(f"{self.cache_prefix}_phase")
        if not phase_data:
            self.current_phase = None
            return None

        if (
            not self.current_phase
            or self.current_phase.name != phase_data['phase']
            or self.current_phase.start_time != phase_data['start_time']
        ):
            self.current_phase = Phase(
                name=phase_data['phase'],
                duration=phase_data['duration'],
                start_time=phase_data['start_time']
            )

        return self.current_phase


    def _on_phase_expire(self, phase: Phase):
        phase_name = phase.name
        expected_start = phase.start_time

        phase = self.get_phase()
        if (not phase
            or phase.name != phase_name
            or phase.start_time != expected_start):
            return

        if phase_name == "hint_phase_start":
            self.set_phase("round_phase_start", 20)
            threading.Thread(
                target=self.event_processor.save_submitted_hints,
                daemon=True
            ).start()
        else:
            self.event_dispatcher.send_reveal_cards()
            result = self.event_processor.finish_check()
            if result:
                self.event_dispatcher.send_game_over(result)

            self.set_phase("hint_phase_start", 10)
            threading.Thread(
                target=self.event_processor.save_picked_words,
                daemon=True
            ).start()

        self.start_phase_cycle()

    def schedule_phase_transition(self, phase_name: str):
        phase = self.get_phase()
        if not phase or phase.name != phase_name:
            return

        phase = Phase(
            name=phase.name,
            duration=phase.duration,
            start_time=phase.start_time
        )
        phase.schedule_transition(self._on_phase_expire)

    def handle_existing_phase(self):
        phase = self.get_phase()
        if not phase:
            return "no_phase"
        
        now = time.time()
        end_time = phase.start_time + phase.duration
        
        if now >= end_time:
            next_phase = "hint_phase_start" if phase.name == "round_phase_start" else "round_phase_start"
            next_duration = 10 if next_phase == "hint_phase_start" else 20
            self.set_phase(next_phase, next_duration)
            self.start_phase_cycle()
        else:
            self.schedule_phase_transition(phase.name)

    def start_phase_cycle(self):
        phase = self.get_phase()
        if not phase:
            return
        
        self.event_dispatcher.send_phase(
            phase_type=phase.name,
            duration=phase.duration,
            start_time=phase.start_time
        )
        self.schedule_phase_transition(phase.name)
    
    def advance_phase(self):
        phase = self.current_phase

        if not phase:
            return
        self._on_phase_expire(self.current_phase)


class GameEventDispatcher:
    def __init__(self, channel_layer, game_group_name, send_handler):
        self.channel_layer = channel_layer
        self.game_group_name = game_group_name
        self.send_handler = send_handler

    def card_choice(self, username, card_id, card_status):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                'type': 'choose_card',
                'username': username,
                'card_id': card_id,
                'card_status': card_status,
            }
        )

    def hint_receive(self, hint_word, hint_num):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                'type': 'hint_display',
                'hint_word': hint_word,
                'hint_num': hint_num
            }
        )

    def sync(self, phase):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "sync_time",
                "duration": phase.duration,
                "phase": phase.name,
                "start_time": phase.start_time
            }
        )

    def send_phase(self, phase_type, duration, start_time):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "phase_event",
                "phase": phase_type,
                "duration": duration,
                "start_time": start_time,
            })
        
    def send_reveal_cards(self):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "reveal_cards"
            }
        )

    def new_player(self, game_id):
        async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {
                    "type": "player_join",
                    "leader_list": list(
                        Player.objects.filter(game=game_id, leader=True).values_list("username", flat=True)
                    )
                }
            )
        
    def send_game_over(self, payload):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "game_over",
                "payload": payload
            }
        )

    def player_join(self, event):
        leader_list = event['leader_list']
        self.send_handler(text_data=json.dumps({
            'action': 'player_join',
            'leader_list': leader_list
        }))

    def choose_card(self, event):
        self.send_handler(text_data=json.dumps({
            'action': 'choose_card',
            'username': event['username'],
            'card_id': event['card_id'],
            'card_status': event['card_status'],
        }))

    def hint_display(self, event):
        self.send_handler(text_data=json.dumps({
            'action': 'hint_display',
            'hint_word': event['hint_word'],
            'hint_num': event['hint_num']
        }))

    def sync_time(self, event):
        self.send_handler(text_data=json.dumps({
            "action": "sync_time",
            "duration": event["duration"],
            "phase": event["phase"],
            "start_time": event['start_time']
        }))

    def reveal_cards(self, event):
        self.send_handler(text_data=json.dumps({
            "action": "reveal_guessed_cards"
        }))

    def phase_event(self, event):
        self.send_handler(text_data=json.dumps({
            "action": event["phase"],
            "duration": event["duration"],
            "start_time": event["start_time"]
        }))

    def game_over(self, event):
        self.send_handler(text_data=json.dumps({
            "action": "game_over",
            **event["payload"]
        }))


class GameEventProcessor:
    def __init__(self, game_id):
        self.game_id = game_id
        self._stored_hint = None
        self._stored_picks = None
        self.picks_received = threading.Event()

    def capture_hint(self, data):
        if self._stored_hint is None:
            self._stored_hint = data

    def save_submitted_hints(self):
        data = self._stored_hint

        if not data:
            return
        
        add_hint(
            Game.objects.get(id=self.game_id),
            data["leaderTeam"],
            data["hintWord"],
            data["hintNum"]
        )
        self._stored_hint = None

    def capture_picks(self, data):
        if self._stored_picks is None:
            self._stored_picks = data
            self.picks_received.set()    

    def save_picked_words(self):
        self.picks_received.wait(timeout=3)
        
        data = self._stored_picks or {}
        picked_words = data.get("pickedCards", [])
        if not picked_words:
            return
        
        game = Game.objects.get(pk=self.game_id)

        with transaction.atomic():
            Card.objects.filter(
                game=game,
                word__in=picked_words
            ).update(is_guessed=True)

        self._stored_picks = None
        self.picks_received.clear()

    def finish_check(self):
        game = Game.objects.get(id=self.game_id)
        red_guesses, blue_guesses, starting_team = game.tally_scores()

        red_wins  = (starting_team == "Red" and red_guesses >= 9) or (starting_team != "Red" and red_guesses >= 8)
        blue_wins = (starting_team == "Blue" and blue_guesses >= 9) or (starting_team != "Blue" and blue_guesses >= 8)

        if red_wins or blue_wins:
            winner = "Red" if red_wins else "Blue"
            game.winners = winner
            game.save(update_fields=['winners'])

            return {
            "winner": winner,
            "red_score": game.red_team_score,
            "blue_score": game.blue_team_score,
            }

        return None