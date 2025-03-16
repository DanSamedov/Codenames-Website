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


        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'team_choice',
                'role': role,
                'team': team,

            }
        )


    def team_choice(self, event):
        role = event['role']
        team = event['team']


        self.send(text_data=json.dumps({
            'role': role,
            'team': team,
        }))