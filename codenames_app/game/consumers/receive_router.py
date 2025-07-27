import json
import logging
from typing import Any, Optional

from .handlers.card_choice import card_choice
from .handlers.hint_submit import hint_submit
from .handlers.picked_words import picked_words
from .constants import ACTION_CARD_CHOICE, ACTION_HINT_SUBMIT, ACTION_PICKED_WORDS, PHASE_HINT

logger = logging.getLogger(__name__)


def receive(consumer: Any, text_data: Optional[str] = None, bytes_data: Optional[bytes] = None) -> None:
    try:
        if not text_data:
            logger.warning("Empty message received.")
            return

        data = json.loads(text_data)
        username = consumer.scope["session"].get("username")

        if not username:
            consumer.send(json.dumps({"error": "User not authenticated."}))
            return

        phase = consumer.phase_manager.get_phase()
        if not phase:
            consumer.send(json.dumps({"error": "No active game phase found."}))
            return

        action = data.get("action")
        logger.debug(f"Received action: {action} from {username}")

        if action == ACTION_CARD_CHOICE:
            card_choice(consumer, data)
        elif action == ACTION_HINT_SUBMIT and phase.name == PHASE_HINT:
            hint_submit(consumer, data)
        elif action == ACTION_PICKED_WORDS:
            picked_words(consumer, data, phase)
        else:
            logger.warning(f"Unknown or invalid action received: {action}")

    except json.JSONDecodeError:
        logger.error("Failed to decode JSON from WebSocket message.")
        consumer.send(json.dumps({"error": "Invalid JSON format."}))
    except Exception as e:
        logger.exception(f"Unhandled exception in receive: {e}")
        consumer.send(json.dumps({"error": "Internal server error."}))
