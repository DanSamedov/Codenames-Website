from room.models import Game
from game.models import Hint 
from django.db import transaction


def add_hint(game, team, hint_word, hint_num):    
    return Hint.objects.create(
        game=game,
        team=team,
        word=hint_word,
        num=hint_num
    )

def get_last_hint(game_id, team):
    try:
        return Hint.objects.filter(
            game_id=game_id, 
            team=team
        ).latest('created_at')
    except Hint.DoesNotExist:
        return None
