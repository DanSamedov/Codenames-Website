import logging
from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
from .connections import connect, disconnect
from .receive_router import receive
from .group_events import GroupEventHandlers

logger = logging.getLogger(__name__)

class RoomConsumer(WebsocketConsumer):
    def connect(self):
        connect(self)

    def disconnect(self, close_code):
        disconnect(self)

    def receive(self, text_data=None, bytes_data=None):
        receive(self, text_data)

    def player_join(self, event):
        GroupEventHandlers.player_join(self, event)

    def team_choice(self, event):
        GroupEventHandlers.team_choice(self, event)

    def restrict_choice(self, event):
        GroupEventHandlers.restrict_choice(self, event)

    def redirect_players(self, event):
        GroupEventHandlers.redirect_players(self, event)

    def unready_players(self, event):
        GroupEventHandlers.unready_players(self, event)

    def player_leave(self, event):
        GroupEventHandlers.player_leave(self, event)
