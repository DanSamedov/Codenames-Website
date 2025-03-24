from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json
from room.models import Player, Game

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

        if self.username:
            async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {
                    "type": "player_join",
                    "username": self.username,
                    "leader_list": list(Player.objects.filter(game=self.game_id, leader=True).values_list("username", flat=True))
                }
            )


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
        
        if data["action"] == "card_choice":
            card_id = data.get("card_id")
            card_status = data.get("card_status")
            self.card_choice(username, card_id, card_status)

        if data["action"] == "hint_submit":
            hint_word = data["hintWord"]
            self.hint_receive(hint_word)


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


    def hint_receive(self, hint_word):
         async_to_sync(self.channel_layer.group_send)(
                self.game_group_name,
                {
                    'type': 'hint_display',
                    'hint_word': hint_word
                }
            )


    def player_join(self, event):
        username = event['username']
        leader_list = event['leader_list']

        self.send(text_data=json.dumps({
            'action': 'player_join',
            'username': username,
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

        self.send(text_data=json.dumps({
            'action': 'hint_display',
            'hint_word': hint_word
        }))