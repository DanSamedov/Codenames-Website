import logging
from asgiref.sync import async_to_sync
from django.core.cache import cache
from django.db.models import ObjectDoesNotExist
from room.models import Player, Game
from game.utils.hints_logic import get_last_hint
from .dispatcher import GameEventSender, GameEventHandler
from .phase import PhaseManager
from .processor import GameEventProcessor
from .constants import PHASE_HINT, HINT_PHASE_DURATION
from typing import Any

logger = logging.getLogger(__name__)

def connect(consumer: Any) -> None:
    try:
        consumer.game_id = consumer.scope['url_route']['kwargs']['id']
        consumer.game_group_name = f'game_{consumer.game_id}'
        consumer.username = consumer.scope["session"].get("username")

        if not consumer.username:
            logger.warning("Connection rejected: username not found in session.")
            consumer.close()
            return

        consumer.cache_selected_cards = f'game_{consumer.game_id}_selected_cards'
        cache.get_or_set(consumer.cache_selected_cards, [])

        async_to_sync(consumer.channel_layer.group_add)(
            consumer.game_group_name,
            consumer.channel_name
        )
        consumer.accept()

        consumer.event_sender = GameEventSender(consumer.channel_layer, consumer.game_group_name)
        consumer.event_handler = GameEventHandler(consumer.send)
        consumer.event_processor = GameEventProcessor(consumer.game_id)
        consumer.phase_manager = PhaseManager(
            consumer.game_id,
            consumer.channel_layer,
            consumer.game_group_name,
            consumer.event_sender,
            consumer.event_processor,
            consumer.cache_selected_cards
        )

        selected_cards = cache.get(consumer.cache_selected_cards, [])
        consumer.event_sender.broadcast_cards(selected_cards)

        consumer.event_sender.new_player(consumer.game_id)

        phase = consumer.phase_manager.get_phase()
        try:
            creator = Player.objects.get(game=consumer.game_id, creator=True)
            game = Game.objects.get(id=consumer.game_id)
        except ObjectDoesNotExist:
            logger.error(f"Game or creator player not found for game_id={consumer.game_id}")
            return

        if not phase and consumer.username == creator.username:
            logger.info(f"Starting new game phase for game {consumer.game_id}")
            consumer.phase_manager.set_phase(phase_name=PHASE_HINT, duration=HINT_PHASE_DURATION, team=game.starting_team)
            consumer.phase_manager.start_phase_cycle()
        elif phase:
            consumer.phase_manager.handle_existing_phase()
            last_hint = get_last_hint(game_id=consumer.game_id)
            payload = {
                "phase": phase.serialize()
            }
            if last_hint:
                payload.update({
                    "hint_word": last_hint.word,
                    "hint_num": last_hint.num
                })
            consumer.event_sender.sync(payload)
    except Exception as e:
        logger.exception(f"Exception during WebSocket connect: {e}")
        consumer.close()


def disconnect(consumer: Any, close_code: int) -> None:
    try:
        async_to_sync(consumer.channel_layer.group_discard)(
            consumer.game_group_name,
            consumer.channel_name
        )
        logger.info(f"Disconnected WebSocket for user={consumer.username} game_id={consumer.game_id}")
    except Exception as e:
        logger.exception(f"Exception during disconnect: {e}")
