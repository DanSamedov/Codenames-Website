import json
import logging
from asgiref.sync import async_to_sync
from room.models import Player
from .actions import change_team, start_game

logger = logging.getLogger(__name__)

def receive(consumer, text_data):
    try:
        data = json.loads(text_data)
        action = data.get("action")
        logger.info(f"Received action: {action} from user: {consumer.username}")

        if not consumer.username:
            consumer.send(text_data=json.dumps({"error": "User not authenticated"}))
            logger.warning("Unauthenticated user tried to send a message.")
            return

        if action == "change_team":
            role = data.get('role')
            team = data.get('team')
            change_team(consumer, role, team)

        elif action == "start_game":
            start_game(consumer)

        elif action == "leave":
            async_to_sync(consumer.channel_layer.group_send)(
                consumer.room_group_name,
                {
                    "type": "player_leave",
                    "username": consumer.username
                }
            )

        else:
            logger.warning(f"Unknown action received: {action}")
            consumer.send(text_data=json.dumps({"error": f"Unknown action: {action}"}))

    except json.JSONDecodeError:
        logger.exception("Invalid JSON received.")
        consumer.send(text_data=json.dumps({"error": "Invalid JSON received"}))
    except Exception as e:
        logger.exception("Unexpected error in receive.")
        consumer.send(text_data=json.dumps({"error": str(e)}))
