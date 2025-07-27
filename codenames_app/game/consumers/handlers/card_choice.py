import json
import logging
from django.core.cache import cache
from typing import Any, Dict

logger = logging.getLogger(__name__)

def card_choice(consumer: Any, data: Dict) -> None:
    try:
        chosen = data.get('card_status')
        cid = data.get('card_id')
        if cid is None or chosen is None:
            raise ValueError("Missing 'card_id' or 'card_status' in payload.")

        with cache.lock(f'card_lock_{consumer.game_id}'):
            selected_cards = cache.get(consumer.cache_selected_cards, [])
            if chosen and cid not in selected_cards:
                selected_cards.append(cid)
            elif not chosen and cid in selected_cards:
                selected_cards.remove(cid)
            cache.set(consumer.cache_selected_cards, selected_cards, timeout=None)

        logger.info(f"Updated selected cards: {selected_cards}")
        consumer.event_sender.broadcast_cards(selected_cards)
    except Exception as e:
        logger.exception(f"Error handling card_choice: {e}")
        consumer.send(json.dumps({"error": "Failed to update card selection."}))