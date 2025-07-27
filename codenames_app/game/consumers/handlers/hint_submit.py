import json
import logging
from typing import Any, Dict
logger = logging.getLogger(__name__)

def hint_submit(consumer: Any, data: Dict) -> None:
    try:
        hint_word = data.get("hintWord")
        hint_num = data.get("hintNum")

        if not hint_word or hint_num is None:
            raise ValueError("Invalid hint submission data.")

        consumer.event_sender.hint_receive(hint_word, hint_num)
        consumer.event_processor.save_submitted_hints(data)
        consumer.phase_manager.advance_phase()
        logger.info(f"Hint submitted: {hint_word} - {hint_num}")
    except Exception as e:
        logger.exception(f"Error handling hint submission: {e}")
        consumer.send(json.dumps({"error": "Failed to submit hint."}))