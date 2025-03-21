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


    def player_join(self, event):
        username = event['username']
        leader_list = event['leader_list']

        self.send(text_data=json.dumps({
            'action': 'player_join',
            'username': username,
            'leader_list': leader_list
        }))    