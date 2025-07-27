import json
import logging
from asgiref.sync import async_to_sync
from room.models import Player
from typing import Any, Dict

logger = logging.getLogger(__name__)


class GameEventSender:
    def __init__(self, channel_layer: Any, game_group_name: str) -> None:
        self.channel_layer = channel_layer
        self.game_group_name = game_group_name
        logger.debug(f"Initialized GameEventSender for '{self.game_group_name}'")

    def _group_send(self, type_: str, **kwargs: Any) -> None:
        logger.debug(f"Group send: {type_}, Data: {kwargs}")
        async_to_sync(self.channel_layer.group_send)(
            self.game_group_name,
            {'type': type_, **kwargs}
        )

    def card_choice(self, username: str, card_id: Any, card_status: Any) -> None:
        logger.info(f"Sending card_choice from {username}: {card_id=} {card_status=}")
        self._group_send('choose_card', username=username, card_id=card_id, card_status=card_status)

    def hint_receive(self, hint_word: str, hint_num: int) -> None:
        logger.info(f"Sending hint: {hint_word=} {hint_num=}")
        self._group_send('hint_display', hint_word=hint_word, hint_num=hint_num)

    def sync(self, payload: Dict[str, Any]) -> None:
        logger.info("Sending sync payload")
        self._group_send('sync_time', payload=payload)

    def send_phase(self, phase_type: str, duration: int, start_time: float, team: str) -> None:
        logger.info(f"Sending phase: {phase_type=} {team=}")
        self._group_send('phase_event', phase=phase_type, duration=duration, team=team, start_time=start_time)

    def send_reveal_cards(self) -> None:
        logger.info("Sending reveal_cards")
        self._group_send('reveal_cards')

    def new_player(self, game_id: Any) -> None:
        leaders = list(
            Player.objects.filter(game=game_id, leader=True).values_list("username", flat=True)
        )
        logger.info(f"Sending new player join with leaders: {leaders}")
        self._group_send('player_join', leader_list=leaders)

    def send_game_over(self, payload: Dict[str, Any]) -> None:
        logger.info(f"Sending game over: {payload}")
        self._group_send('game_over', payload=payload)

    def broadcast_cards(self, selected_cards: Any) -> None:
        logger.info("Broadcasting selected cards")
        self._group_send('selected_cards', cards=selected_cards)


class GameEventHandler:
    def __init__(self, send_handler: Any) -> None:
        self.send_handler = send_handler

    def _send_json(self, data: Dict[str, Any]) -> None:
        self.send_handler(text_data=json.dumps(data))

    def _send_action(self, action: str, **kwargs: Any) -> None:
        self._send_json({
            "action": action,
            **kwargs
        })

    def selected_cards(self, event: Dict[str, Any]) -> None:
        logger.debug("Handling selected_cards event")
        self._send_action('selected_cards', cards=event['cards'])

    def player_join(self, event: Dict[str, Any]) -> None:
        logger.debug("Handling player_join event")
        self._send_action('player_join', leader_list=event['leader_list'])

    def choose_card(self, event: Dict[str, Any]) -> None:
        logger.debug("Handling choose_card event")
        self._send_action(
            'choose_card',
            username=event['username'],
            card_id=event['card_id'],
            card_status=event['card_status']
        )

    def hint_display(self, event: Dict[str, Any]) -> None:
        logger.debug("Handling hint_display event")
        self._send_action(
            'hint_display',
            hint_word=event['hint_word'],
            hint_num=event['hint_num']
        )

    def sync_time(self, event: Dict[str, Any]) -> None:
        logger.debug("Handling sync_time event")
        self._send_action('sync_time', **event['payload'])

    def reveal_cards(self, event: Dict[str, Any]) -> None:
        logger.debug("Handling reveal_cards event")
        self._send_action('reveal_guessed_cards')

    def phase_event(self, event: Dict[str, Any]) -> None:
        logger.debug("Handling phase_event")
        self._send_action(
            event['phase'],
            duration=event['duration'],
            team=event['team'],
            start_time=event['start_time']
        )

    def game_over(self, event: Dict[str, Any]) -> None:
        logger.debug("Handling game_over event")
        self._send_action('game_over', **event['payload'])