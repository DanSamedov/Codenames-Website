import json
import time
import threading
from dataclasses import dataclass, field
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync, sync_to_async
from room.models import Player, Game
from game.utils.hints_logic import add_hint, get_last_hint
from game.utils.guesses_logic import add_guess
from django.core.cache import cache


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

        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "player_join",
                "leader_list": list(
                    Player.objects.filter(game=self.game_id, leader=True).values_list("username", flat=True)
                )
            }
        )

        game_phase_data = self.phase_manager.get_phase()
        creator_username = Player.objects.get(game=self.game_id, creator=True).username

        if not game_phase_data and self.username == creator_username:
            self.phase_manager.set_phase("hint_phase_start", 10)
            self.phase_manager.start_phase_cycle()
        elif game_phase_data:
            self.phase_manager.handle_existing_phase()
            self.event_dispatcher.sync(game_phase_data)

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

        game_phase_data = self.phase_manager.get_phase()
        if not game_phase_data:
            self.send(text_data=json.dumps({"error": "No game phase found"}))
            return

        action = data.get("action")
        current_phase = game_phase_data["phase"]
        
        if action == "card_choice" and current_phase == "round_phase_start":
            self.event_dispatcher.card_choice(
                username, 
                card_id=data.get("card_id"), 
                card_status=data.get("card_status")
            )
        elif action == "hint_submit" and current_phase == "hint_phase_start":
            self.event_dispatcher.hint_receive(data["hintWord"], data["hintNum"])
            self.event_processor.capture_hint(data)
        elif action == "picked_cards":
            print(f"recieve{data}")
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

    def get_phase(self):
        phase_data = cache.get(f"{self.cache_prefix}_phase")
        if not phase_data:
            return None
        
        if not self.current_phase or self.current_phase.name != phase_data['phase']:
            self.current_phase = Phase(
                name=phase_data['phase'],
                duration=phase_data['duration'],
                start_time=phase_data['start_time']
            )
        return phase_data

    def schedule_phase_transition(self, phase_name):
        current_phase_data = self.get_phase()
        if not current_phase_data or current_phase_data['phase'] != phase_name:
            return

        lock_key = f"{self.cache_prefix}_scheduler_{phase_name}"
        lock_acquired = cache.add(lock_key, True, timeout=current_phase_data['duration'] + 2)
        if not lock_acquired:
            return

        expected_start = current_phase_data['start_time']
        
        def on_phase_expire(phase):
            try:
                current_data = self.get_phase()
                if not current_data or current_data['phase'] != phase_name or current_data['start_time'] != expected_start:
                    return
                
                if phase_name == "hint_phase_start":
                    self.set_phase("round_phase_start", 20)
                    threading.Thread(
                        target=self.event_processor.save_submitted_hints,
                        daemon=True
                    ).start()
                elif phase_name == "round_phase_start":
                    self.event_dispatcher.send_reveal_cards()
                    self.set_phase("hint_phase_start", 10)
                    threading.Thread(
                        target=self.event_processor.save_picked_cards,
                        daemon=True
                    ).start()
                self.start_phase_cycle()
            finally:
                cache.delete(lock_key)

        phase = Phase(
            name=phase_name,
            duration=current_phase_data['duration'],
            start_time=current_phase_data['start_time']
        )
        phase.schedule_transition(on_phase_expire)

    def handle_existing_phase(self):
        phase_data = self.get_phase()
        if not phase_data:
            return "no_phase"
        
        now = time.time()
        end_time = phase_data['start_time'] + phase_data['duration']
        
        if now >= end_time:
            next_phase = "hint_phase_start" if phase_data['phase'] == "round_phase_start" else "round_phase_start"
            next_duration = 10 if next_phase == "hint_phase_start" else 20
            self.set_phase(next_phase, next_duration)
            self.start_phase_cycle()
        else:
            self.schedule_phase_transition(phase_data['phase'])

    def start_phase_cycle(self):
        phase_data = self.get_phase()
        if not phase_data:
            return
        
        self.event_dispatcher.send_phase(
            phase_type=phase_data["phase"],
            duration=phase_data["duration"],
            start_time=phase_data["start_time"]
        )
        self.schedule_phase_transition(phase_data["phase"])


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

    def sync(self, phase_data):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "sync_time",
                "duration": phase_data["duration"],
                "phase": phase_data["phase"],
                "start_time": phase_data["start_time"]
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


class GameEventProcessor:
    def __init__(self, game_id):
        self.game_id = game_id
        self._stored_hint = None
        self._stored_picks = None


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
        print(f"capture_picks: {self._stored_picks}")
    

    def save_picked_cards(self):
        data = self._stored_picks
        if not data:
            return
        print(f"save_picked_cards: {self._stored_picks}")

        picked_cards = data.get("pickedCards", [])
        hint = get_last_hint(self.game_id)
        if hint and picked_cards:
            add_guess(picked_cards, hint)
        self._stored_picks = None
