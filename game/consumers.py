import json, time
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from room.models import Player, Game
from game.utils.hints_logic import add_hint


class GameConsumer(WebsocketConsumer):
    def connect(self):
        self.game_id = self.scope['url_route']['kwargs']['id']
        self.game_group_name = f'game_{self.game_id}'
        self.current_phase = 'hint'

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

        # synchronize timer time with server
        self.sync()

        # self.hint_phase()
        self.start_phase_cycle()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.game_group_name,
            self.channel_name
        )


    def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        print(f"Received message: {data}")  # Debug log

        username = self.scope["session"].get("username")
        if not username:
            self.send(text_data=json.dumps({"error": "User not authenticated"}))
            return
        
        if data["action"] == "card_choice" and self.current_phase == "round":
            card_id = data.get("card_id")
            card_status = data.get("card_status")

            self.card_choice(username, card_id, card_status)

        if data["action"] == "hint_submit" and self.current_phase == "hint":
            hint_word = data["hintWord"]
            hint_num = data["hintNum"]
            leader_team = data["leaderTeam"]

            add_hint(Game.objects.get(id=self.game_id), leader_team, hint_word, hint_num)
            self.hint_receive(hint_word, hint_num)

        if data["action"] == "start_round":
            print(f"Starting round, current phase: {self.current_phase}")  # Debug log
            self.current_phase = 'round'
            self.start_phase_cycle()

        if data["action"] == "start_timer":
            print(f"Timer ended, current phase: {self.current_phase}")  # Debug log
            # Toggle the phase
            if self.current_phase == 'round':
                self.current_phase = 'hint'
            else:
                self.current_phase = 'round'
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
        if self.current_phase == 'round':
            # Start round phase with 20-second duration
            duration = 20
            start_time = int(time.time())
            async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {
                    "type": "round_start",
                    "duration": duration,
                    "start_time": start_time,
                }
            )
        else:
            # Start hint phase with 10-second duration
            duration = 10
            start_time = int(time.time())
            async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {
                    "type": "hint_timer_start",
                    "duration": duration,
                    "start_time": start_time,
                }
            )


    def sync(self):
        async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {
                    "type": "sync_time",
                    "server_time": int(time.time())
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

    # synchronize timer time with server
    def sync_time(self, event):
        server_time = event['server_time']

        self.send(text_data=json.dumps({
            "action": "sync_time",
            "server_time": server_time
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
