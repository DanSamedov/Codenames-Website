import logging
import re
from asgiref.sync import async_to_sync
from room.models import Player

logger = logging.getLogger(__name__)

def connect(consumer):
    consumer.room_id = consumer.scope['url_route']['kwargs']['id']
    consumer.room_group_name = f'room_{consumer.room_id}'
    consumer.username = consumer.scope["session"].get("username", "").strip()

    if not consumer.username:
        logger.warning("Connection attempt without username.")
        consumer.close()
        return

    consumer.user_group_name = f"user_{re.sub(r'[^a-zA-Z0-9_.-]', '_', consumer.username)}"
    async_to_sync(consumer.channel_layer.group_add)(consumer.room_group_name, consumer.channel_name)
    async_to_sync(consumer.channel_layer.group_add)(consumer.user_group_name, consumer.channel_name)

    consumer.accept()
    logger.info(f"User connected: {consumer.username} to room {consumer.room_id}")

    new_player = Player.objects.filter(game=consumer.room_id, username=consumer.username).first()
    async_to_sync(consumer.channel_layer.group_send)(
        consumer.room_group_name,
        {
            "type": "player_join",
            "username": new_player.username,
            "role": new_player.leader,
            "team": new_player.team
        }
    )

def disconnect(consumer):
    logger.info(f"User disconnected: {consumer.username} from room {consumer.room_id}")
    async_to_sync(consumer.channel_layer.group_discard)(consumer.room_group_name, consumer.channel_name)
    async_to_sync(consumer.channel_layer.group_discard)(consumer.user_group_name, consumer.channel_name)
