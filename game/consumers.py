import json
import time
import threading
import math
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

        game_phase = self.phase_manager.get_phase()
        creator_username = Player.objects.get(game=self.game_id, creator=True).username

        if not game_phase and self.username == creator_username:
            self.phase_manager.set_phase("hint_phase_start", 10)
            self.phase_manager.start_phase_cycle()
        elif game_phase:
            self.phase_manager.handle_existing_phase()
            self.event_dispatcher.sync(game_phase)

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

        game_phase = self.phase_manager.get_phase()
        if not game_phase:
            self.send(text_data=json.dumps({"error": "No game phase found"}))
            return

        action = data.get("action")
        if action == "card_choice" and game_phase["phase"] == "round_phase_start":
            self.event_dispatcher.card_choice(
                username, 
                card_id=data.get("card_id"), 
                card_status=data.get("card_status")
            )
        elif action == "hint_submit" and game_phase["phase"] == "hint_phase_start":
            self.event_dispatcher.hint_receive(data["hintWord"], data["hintNum"])
            self.event_processor.capture_hint(data)
            self.phase_manager.set_phase("round_phase_start", 20)
            self.phase_manager.start_phase_cycle()
        elif action == "picked_cards":
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


class PhaseManager:
    def __init__(self, game_id, channel_layer, game_group_name, event_dispatcher, event_processor):
        self.game_id = game_id
        self.cache_prefix = f"game_{self.game_id}"
        self.channel_layer = channel_layer
        self.game_group_name = game_group_name
        self.event_dispatcher = event_dispatcher
        self.event_processor = event_processor


    def set_phase(self, phase, duration):
        start_time = int(time.time())
        cache.set(
            f"{self.cache_prefix}_phase",
            {
                'phase': phase,
                'duration': duration,
                'start_time': start_time,
            },
            timeout=duration
        )


    def get_phase(self):
        return cache.get(f"{self.cache_prefix}_phase")


    def schedule_phase_transition(self, phase):
        current_phase = self.get_phase()
        if not current_phase or current_phase['phase'] != phase:
            return

        lock_key = f"{self.cache_prefix}_scheduler_{phase}"
        lock_acquired = cache.add(lock_key, True, timeout=current_phase['duration'] + 2)
        if not lock_acquired:
            return

        expected_start = current_phase['start_time']
        expected_duration = current_phase['duration']

        def transition():
            try:
                now = time.time()
                remaining = (expected_start + expected_duration) - now
                if remaining > 0:
                    time.sleep(remaining)
                
                current_phase_after = self.get_phase()
                valid = (
                    current_phase_after and
                    current_phase_after['phase'] == phase and
                    current_phase_after['start_time'] == expected_start
                )
                
                if valid:
                    if phase == "hint_phase_start":
                        self.set_phase("round_phase_start", 20)
                        threading.Thread(
                            target=self.event_processor.save_submitted_hints,
                            daemon=True
                        ).start()
                    elif phase == "round_phase_start":
                        self.event_dispatcher.send_reveal_cards()
                        self.set_phase("hint_phase_start", 10)
                        threading.Thread(
                            target=self.event_processor.save_picked_cards,
                            daemon=True
                        ).start()
                    self.start_phase_cycle()
            finally:
                cache.delete(lock_key)
        threading.Thread(target=transition, daemon=True).start()


    def handle_existing_phase(self):
        phase = self.get_phase()
        if not phase:
            return "no_phase"
        
        now = int(time.time())
        end_time = phase['start_time'] + phase['duration']
        if now >= end_time:
            next_phase = "hint_phase_start" if phase['phase'] == "round_phase_start" else "round_phase_start"
            self.set_phase(next_phase, 10 if next_phase == "hint_phase_start" else 20)
            self.start_phase_cycle()
        else:
            self.schedule_phase_transition(phase['phase'])


    def start_phase_cycle(self):
        game_phase = self.get_phase()
        self.event_dispatcher.send_phase(
            phase_type=game_phase["phase"],
            duration=game_phase["duration"],
            start_time=game_phase["start_time"]
        )
        self.schedule_phase_transition(game_phase["phase"])


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


    def sync(self, game_phase):
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "sync_time",
                "duration": game_phase["duration"],
                "phase": game_phase["phase"],
                "start_time": game_phase["start_time"]
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

    
    def save_picked_cards(self):
        data = self._stored_picks
        print(data)
        if not data:
            return
        
        picked_cards = data["pickedCards"]
        hint = get_last_hint(self.game_id)
        if hint and picked_cards:
            add_guess(picked_cards, hint)
        self._stored_picks = None
