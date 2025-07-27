from channels.generic.websocket import WebsocketConsumer
from typing import Optional, Dict

from .connections import connect, disconnect
from .receive_router import receive


class GameConsumer(WebsocketConsumer):
    def connect(self) -> None:
        connect(self)

    def disconnect(self, close_code: int) -> None:
        disconnect(self, close_code)

    def receive(self, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None) -> None:
        receive(self, text_data, bytes_data)

    def player_join(self, event: Dict) -> None:
        self.event_handler.player_join(event)

    def choose_card(self, event: Dict) -> None:
        self.event_handler.choose_card(event)

    def hint_display(self, event: Dict) -> None:
        self.event_handler.hint_display(event)

    def sync_time(self, event: Dict) -> None:
        self.event_handler.sync_time(event)

    def phase_event(self, event: Dict) -> None:
        self.event_handler.phase_event(event)

    def reveal_cards(self, event: Dict) -> None:
        self.event_handler.reveal_cards(event)

    def game_over(self, event: Dict) -> None:
        self.event_handler.game_over(event)

    def selected_cards(self, event: Dict) -> None:
        self.event_handler.selected_cards(event)
