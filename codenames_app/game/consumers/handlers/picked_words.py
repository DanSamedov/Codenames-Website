import json
import logging
from typing import Any, Dict
logger = logging.getLogger(__name__)

def picked_words(consumer: Any, data: Dict, phase: Any) -> None:
    try:
        data["team"] = phase.team
        payload = consumer.event_processor.save_picked_words(data)
        if payload:
            consumer.event_sender.send_game_over(payload)
            logger.info(f"Game over triggered for game {consumer.game_id}")
    except Exception as e:
        logger.exception(f"Error handling picked words: {e}")
        consumer.send(json.dumps({"error": "Failed to submit picked words."}))