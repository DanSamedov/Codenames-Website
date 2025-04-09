import json, time
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from room.models import Player, Game
from game.utils.hints_logic import add_hint
from django.core.cache import cache


class GameConsumer(WebsocketConsumer):
    def set_phase(self, phase, duration):
        start_time = int(time.time())
        cache.set(f"game_{self.game_id}_phase", {
            'phase': phase,
            'duration': duration,
            'start_time': start_time,
        }, timeout=duration + 5)


    def get_phase(self):
        return cache.get(f"game_{self.game_id}_phase")


    def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['id']
        self.game_group_name = f'game_{self.game_id}'
        self.username = self.scope["session"].get("username")

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
        
        game_phase = self.get_phase()

        if not game_phase and  self.username == Player.objects.get(game=self.game_id, creator=True).username:
            self.set_phase("hint", 10)
            self.start_phase_cycle()

        if game_phase:
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
            self.send(text_data=json.dumps({"error": "User not authenticated"}))
            return
        
        game_phase = self.get_phase()
        if not game_phase:
            self.send(text_data=json.dumps({"error": "No game phase found"}))
            return
        
        if data["action"] == "card_choice" and game_phase["phase"] == "round":
            card_id = data.get("card_id")
            card_status = data.get("card_status")

            self.card_choice(username, card_id, card_status)

        if data["action"] == "hint_submit" and game_phase["phase"] == "hint":
            hint_word = data["hintWord"]
            hint_num = data["hintNum"]
            leader_team = data["leaderTeam"]

            add_hint(Game.objects.get(id=self.game_id), leader_team, hint_word, hint_num)

            self.hint_receive(hint_word, hint_num)

        if data["action"] == "start_timer":
            now = int(time.time())

            is_timer_cycle = data["type"] == "timer_cycle"
            phase_end_time = game_phase["start_time"] + game_phase["duration"]

            if is_timer_cycle and now < phase_end_time:
                return

            next_phase = "hint" if game_phase["phase"] == "round" else "round"
            duration = 10 if next_phase == "hint" else 20

            self.set_phase(next_phase, duration)
            self.start_phase_cycle()

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
