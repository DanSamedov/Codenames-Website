import json
import time
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from room.models import Player, Game
from game.utils.hints_logic import add_hint, get_last_hint
from game.utils.guesses_logic import add_guess
from django.core.cache import cache
import threading


class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['id']
        self.game_group_name = f'game_{self.game_id}'
        self.username = self.scope["session"].get("username")
        self.phase_manager = PhaseManager(self.game_id, self.channel_layer, self.game_group_name)

        async_to_sync(self.channel_layer.group_add)(
            self.game_group_name,
            self.channel_name
        )
        self.accept()

        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {
                "type": "player_join",
                "leader_list": list(Player.objects.filter(game=self.game_id, leader=True).values_list("username", flat=True))
            }
        )
        
        game_phase = self.phase_manager.get_phase()
        creator_username = Player.objects.get(game=self.game_id, creator=True).username

        if not game_phase and self.username == creator_username:
            self.phase_manager.set_phase("hint", 10)
            self.phase_manager.start_phase_cycle()
        elif game_phase:
            self.phase_manager.handle_existing_phase()
            self.sync(game_phase)


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
        
        if data["action"] == "card_choice" and game_phase["phase"] == "round":
            self.card_choice(username, 
                             card_id=data.get("card_id"), 
                             card_status=data.get("card_status"))

        if data["action"] == "hint_submit" and game_phase["phase"] == "hint":
            self.handle_hint_submission(data)

        if data["action"] == "picked_cards":
            picked_cards = data["pickedCards"]

            hint = get_last_hint(self.game_id)
            if not hint:
                return

            add_guess(picked_cards, hint)


    def handle_hint_submission(self, data):
        self.phase_manager.set_phase("round", 20)
        add_hint(
            Game.objects.get(id=self.game_id),
            data["leaderTeam"],
            data["hintWord"],
            data["hintNum"]
        )
        self.hint_receive(data["hintWord"], data["hintNum"])
        self.phase_manager.start_phase_cycle()
    

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
    

    def player_join(self, event):
        leader_list = event['leader_list']

        self.send(text_data=json.dumps({
            'action': 'player_join',
            'leader_list': leader_list
        }))    

    
    def choose_card(self, event):
        username = event['username']
        card_id = event['card_id']
        card_status = event['card_status']

        self.send(text_data=json.dumps({
            'action':'choose_card',
            'username': username,
            'card_id': card_id,
            'card_status': card_status,
        }))


    def hint_display(self, event):
        hint_word = event['hint_word']
        hint_num = event['hint_num']

        self.send(text_data=json.dumps({
            'action': 'hint_display',
            'hint_word': hint_word,
            'hint_num': hint_num
        }))


    def sync_time(self, event):
        duration = event["duration"]
        phase = event["phase"]
        start_time = event['start_time']

        self.send(text_data=json.dumps({
            "action": "sync_time",
            "duration": duration,
            "phase": phase,
            "start_time": start_time
        }))

    #start round
    def round_start(self, event):
        duration = event['duration']
        start_time = event['start_time']

        self.send(text_data=json.dumps({
            "action": "round_start",
            "duration": duration,
            "start_time": start_time
        }))


    def hint_timer_start(self, event):
        duration = event['duration']
        start_time = event['start_time']

        self.send(text_data=json.dumps({
            "action": "hint_timer_start",
            "duration": duration,
            "start_time": start_time
        }))


    def reveal_cards(self, event):
        self.send(text_data=json.dumps({
            "action": "reveal_guessed_cards"
        }))


class PhaseManager:
    def __init__(self, game_id, channel_layer, game_group_name):
        self.game_id = game_id
        self.channel_layer = channel_layer
        self.game_group_name = game_group_name
        self.cache_prefix = f"game_{self.game_id}"
        

    def set_phase(self, phase, duration):
        start_time = int(time.time())
        cache.set(f"{self.cache_prefix}_phase", {
            'phase': phase,
            'duration': duration,
            'start_time': start_time,
        }, timeout=duration + 5)


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
                time.sleep(max(remaining, 1))
                
                current_phase_after = self.get_phase()
                valid = (
                    current_phase_after and 
                    current_phase_after['phase'] == phase and
                    current_phase_after['start_time'] == expected_start
                )
                
                if valid:

                    if phase == "round":
                         async_to_sync(self.channel_layer.group_send)(
                            self.game_group_name,
                            {
                                "type": "reveal_cards"
                            })
                         
                    next_phase = "hint" if phase == "round" else "round"
                    next_duration = 10 if next_phase == "hint" else 20
                    self.set_phase(next_phase, next_duration)
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
            next_phase = "hint" if phase['phase'] == "round" else "round"
            self.set_phase(next_phase, 10 if next_phase == "hint" else 20)
            self.start_phase_cycle()
        else:
            self.schedule_phase_transition(phase['phase'])


    def start_phase_cycle(self):
        game_phase = self.get_phase()

        if game_phase["phase"] == "round":
            async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {
                    "type": "round_start",
                    "duration": game_phase["duration"],
                    "start_time": game_phase["start_time"],
                }
            )
        else:
            async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {
                    "type": "hint_timer_start",
                    "duration": game_phase["duration"],
                    "start_time": game_phase["start_time"],
                }
            )

        self.schedule_phase_transition(game_phase["phase"])
