from room.models import Game
from game.models import Hint 


def add_hint(game, team, hint_word, hint_num):    
    return Hint.objects.create(
        game=game,
        team=team,
        word=hint_word,
        num=hint_num
    )


def get_last_hint(game_id):
    try:
        return Hint.objects.filter(
            game_id=game_id, 
        ).latest('created_at')
    except Hint.DoesNotExist:
        return None
