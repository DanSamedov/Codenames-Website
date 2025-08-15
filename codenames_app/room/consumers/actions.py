import logging
from asgiref.sync import async_to_sync
from room.models import Player, Game, Card
from game.utils.cards_logic import generate_cards

logger = logging.getLogger(__name__)

def change_team(consumer, role, team):
    current_player = Player.objects.filter(game=consumer.room_id, username=consumer.username).first()

    if not current_player.ready:
        current_player.leader = role
        current_player.team = team
        current_player.ready = True
        current_player.save()

        logger.info(f"{consumer.username} changed team to {team} with role {role} in room {consumer.room_id}")

        async_to_sync(consumer.channel_layer.group_send)(
            consumer.room_group_name,
            {
                'type': 'team_choice',
                'username': consumer.username,
                'role': role,
                'team': team,
            }
        )
    else:
        logger.info(f"{consumer.username} tried to change team after cards were already generated.")
        async_to_sync(consumer.channel_layer.group_send)(
            consumer.user_group_name,
            {
                "type": "restrict_choice", 
            }
        )

def start_game(consumer):
    game_obj = Game.objects.get(pk=consumer.room_id)
    players = Player.objects.filter(game=consumer.room_id)

    if players.count() == players.filter(ready=True).count():
        if Card.objects.filter(game=game_obj).exists():
            logger.info(f"Game already started. Redirecting user {consumer.username} in room {consumer.room_id}.")
            async_to_sync(consumer.channel_layer.group_send)(
                consumer.user_group_name,
                {
                    "type": "redirect_players", 
                    "room_id": consumer.room_id
                }
            )
        else:
            logger.info(f"All players ready. Starting game in room {consumer.room_id}")
            generate_cards(game_obj)
            async_to_sync(consumer.channel_layer.group_send)(
                consumer.room_group_name,
                {
                    "type": "redirect_players",
                    "room_id": consumer.room_id,
                }
            )
    else:
        creator = players.filter(creator=True).first()
        logger.info(f"Not all players ready. Informing creator: {creator.username}")
        async_to_sync(consumer.channel_layer.group_send)(
            consumer.room_group_name,
            {
                "type": "unready_players",
                "creator": creator.username
            }
        )
