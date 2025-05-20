import json
import time
import threading
from dataclasses import dataclass, field
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from room.models import Player, Game
from game.models import Card
from game.utils.hints_logic import add_hint, get_last_hint
from django.core.cache import cache
from django.db import transaction

class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['id']
        self.game_group_name = f'game_{self.game_id}'
        self.username = self.scope["session"].get("username")

        self.cache_key = f'game_{self.game_id}_selected_cards'
        if not cache.get(self.cache_key):
            cache.set(self.cache_key, [], timeout=None)
        
        async_to_sync(self.channel_layer.group_add)(
            self.game_group_name,
            self.channel_name
        )
        self.accept()

        self.event_dispatcher = GameEventDispatcher(self.channel_layer, self.game_group_name, self.send)
        self.event_processor = GameEventProcessor(self.game_id)
        self.phase_manager = PhaseManager(self.game_id, self.channel_layer, self.game_group_name, self.event_dispatcher, self.event_processor)

        selected_cards = cache.get(self.cache_key, [])
        self.event_dispatcher.broadcast_cards(selected_cards)

        self.event_dispatcher.new_player(self.game_id)

        phase = self.phase_manager.get_phase()
        creator_username = Player.objects.get(game=self.game_id, creator=True).username
        starting_team = Game.objects.get(id=self.game_id).starting_team

        if not phase and self.username == creator_username:
            self.phase_manager.set_phase(phase_name="hint_phase", duration=10, team=starting_team)
            self.phase_manager.start_phase_cycle()
        elif phase:
            self.phase_manager.handle_existing_phase()
            last_hint=get_last_hint(game_id=self.game_id)
            payload = {}
            if last_hint:
                payload["hint_word"] = last_hint.word
                payload["hint_num"] = last_hint.num
            
            payload["phase"] = phase.serialize()
            
            self.event_dispatcher.sync(payload)

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
        
        if action == 'card_choice':
            chosen = data['card_status']
            cid = data['card_id']
            
            with cache.lock(f'card_lock_{self.game_id}'):
                selected_cards = cache.get(self.cache_key, [])
                if chosen and cid not in selected_cards:
                    selected_cards.append(cid)
                elif not chosen and cid in selected_cards:
                    selected_cards.remove(cid)
                cache.set(self.cache_key, selected_cards, timeout=None)
            self.event_dispatcher.broadcast_cards(selected_cards)
        elif action == "hint_submit" and phase_name == "hint_phase":
            self.event_dispatcher.hint_receive(data["hintWord"], data["hintNum"])
            self.event_processor.save_submitted_hints(data)
            self.phase_manager.advance_phase()
        elif action == "picked_words":
            data["team"] = phase.team
            payload = self.event_processor.save_picked_words(data)
            if payload:
                self.reset_round_state()
                self.event_dispatcher.send_game_over(payload)

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
    
    def selected_cards(self, event):
        self.event_dispatcher.selected_cards(event)

@dataclass
class Phase:
    name: str
    duration: int
    team: str
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
            "team": self.team,
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

    def set_phase(self, phase_name: str, duration: int, team: str):
        self.current_phase = Phase(name=phase_name, duration=duration, team=team)
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
            or self.current_phase.team != phase_data['team']
            or self.current_phase.start_time != phase_data['start_time']
        ):
            self.current_phase = Phase(
                name=phase_data['phase'],
                duration=phase_data['duration'],
                team = phase_data['team'],
                start_time=phase_data['start_time'],
            )

        return self.current_phase

    def _on_phase_expire(self, phase: Phase):
        phase_name = phase.name
        phase_team = phase.team
        expected_start = phase.start_time

        game = Game.objects.get(pk=self.game_id)
        if game.winners:
            return
        
        phase = self.get_phase()
        if (not phase
            or phase.name != phase_name
            or phase.start_time != expected_start
            or phase.team != phase_team):
            return
        
        next_team = "Red" if phase_team == "Blue" else "Blue"

        if phase_name == "hint_phase":
            self.set_phase(phase_name="round_phase", duration=20, team=phase.team)
        else:
            self.event_dispatcher.send_reveal_cards()
            self.set_phase(
                phase_name="hint_phase",
                duration=10,
                team=next_team
            )
        self.start_phase_cycle()

    def schedule_phase_transition(self, phase_name: str):
        phase = self.get_phase()
        if not phase or phase.name != phase_name:
            return

        phase = Phase(
            name=phase.name,
            duration=phase.duration,
            team=phase.team,
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
            next_phase = "hint_phase" if phase.name == "round_phase" else "round_phase"
            next_duration = 10 if next_phase == "hint_phase" else 20
            if next_phase == "round_phase":
                next_team = "Red" if phase.team == "Blue" else "Blue"
            else:
                next_team = phase.team
            self.set_phase(phase_name=next_phase, duration=next_duration, team=next_team)
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
            team=phase.team,
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

    def sync(self, payload):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "sync_time",
                "payload": payload

            }
        )

    def send_phase(self, phase_type, duration, start_time, team):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "phase_event",
                "phase": phase_type,
                "duration": duration,
                "team": team,
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

    def broadcast_cards(self, selected_cards):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                'type': 'selected_cards',
                'cards': selected_cards
            }
        )

    def selected_cards(self, event):
        self.send_handler(text_data=json.dumps({
            'action': 'selected_cards',
            'cards': event['cards']
            }))

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
            **event["payload"]
        }))

    def reveal_cards(self, event):
        self.send_handler(text_data=json.dumps({
            "action": "reveal_guessed_cards"
        }))

    def phase_event(self, event):
        self.send_handler(text_data=json.dumps({
            "action": event["phase"],
            "duration": event["duration"],
            "team": event["team"],
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

    def save_submitted_hints(self, data):
        if not data:
            return

        with transaction.atomic():
            game = Game.objects.get(id=self.game_id)
            add_hint(
                game,
                data["leaderTeam"],
                data["hintWord"],
                data["hintNum"]
            )

    def save_picked_words(self, data):
        if not data:
            return None

        with transaction.atomic():
            game = Game.objects.get(pk=self.game_id)
            picked_words = data["pickedCards"]
            team = data["team"]

            potential_assassin = Card.objects.filter(
                game=game,
                word__in=picked_words,
                color='Black'
            ).first()

            if potential_assassin:
                Card.objects.filter(pk=potential_assassin.pk).update(is_guessed=True)
                
                winner = team
                game.winners = winner
                game.save(update_fields=['winners'])
                return self.game_over_payload(winner=winner, reason="assassin_picked", game=game)

            picked_cards = Card.objects.filter(
                game=game,
                word__in=picked_words
            )
            picked_cards.update(is_guessed=True)

            instant_win_payload = self.check_instant_win(game)
            if instant_win_payload:
                return instant_win_payload

            return None

    def check_instant_win(self, game: Game):
        with transaction.atomic():
            red_guesses, blue_guesses, starting_team = game.tally_scores()

            red_wins  = (starting_team == "Red" and red_guesses >= 9) or (starting_team != "Red" and red_guesses >= 8)
            blue_wins = (starting_team == "Blue" and blue_guesses >= 9) or (starting_team != "Blue" and blue_guesses >= 8)
            
            if red_wins and blue_wins:
                game.winners = "Draw"
                game.save(update_fields=['winners'])
                return self.game_over_payload(winner="Draw", reason="all_cards_guessed", game=game)
            elif red_wins or blue_wins:
                winner = "Red" if red_wins else "Blue"
                game.winners = winner
                game.save(update_fields=['winners'])

                return self.game_over_payload(winner=winner, reason="all_cards_guessed", game=game)

            return None

    def game_over_payload(self, winner: str, reason: str, game: Game):
        return {
            "winner": winner,
            "reason": reason,
            "red_score": game.red_team_score,
            "blue_score": game.blue_team_score
        }