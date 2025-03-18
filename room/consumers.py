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
        data = json.loads(text_data)
        role = data.get('role')
        team = data.get('team')
        room_id = data.get('room_id')

        username = self.scope["session"].get("username")
        if not username:
            self.send(text_data=json.dumps({"error": "User not authenticated"}))
            return
        
        if data["action"] == "change_team":
            self.change_team(username, role, team)

        elif data["action"] == "start_game":
            self.start_game(room_id)


    def change_team(self, username, role, team):
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
                    'username': username,
                    'role': role,
                    'team': team,

                }
            )


    def start_game(self, room_id):
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                "type": "redirect_players",
                "room_id": room_id,
            }
        )


    def team_choice(self, event):
        username = event['username']
        role = event['role']
        team = event['team']

        self.send(text_data=json.dumps({
            'action':'team_choice',
            'username': username,
            'role': role,
            'team': team,
        }))


    def redirect_players(self, event):
        room_id = event['room_id']

        self.send(text_data=json.dumps({
            'action':'redirect',
            "room_id": room_id,
        }))