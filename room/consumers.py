from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json

class RoomConsumer(WebsocketConsumer):
    def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['id']
        self.room_group_name = f'room_{self.room_id}'

        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )

        self.accept()


    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )


    def receive(self, text_data=None, bytes_data=None):
        user_data = json.loads(text_data)
        role = user_data.get('role')
        team = user_data.get('team')

        username = self.scope["session"].get("username")
        if not username:
            self.send(text_data=json.dumps({"error": "User not authenticated"}))
            return

        from room.models import Player, Game
        current_player = Player.objects.filter(game=self.room_id, username=username).first()

        if current_player:
            current_player.leader = role
            current_player.team = team
            current_player.save()

            async_to_sync(self.channel_layer.group_send)(
                self.room_group_name,
                {
                    'type': 'team_choice',
                    'role': role,
                    'team': team,

                }
            )

        else:
            self.send(text_data=json.dumps({"error": "Player not found"}))


    def team_choice(self, event):
        role = event['role']
        team = event['team']


        self.send(text_data=json.dumps({
            'role': role,
            'team': team,
        }))