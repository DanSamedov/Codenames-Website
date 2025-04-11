from game.models import Guess, Hint
from room.models import Game

def add_guess(game_id, guess, team, ):
    game = Game.objects.get(id=game_id)
    hint = Hint.objects.get(game=game)

    try:
        guess_obj = Guess.objects.create(
            game=game,
            team=team,
            guess=guess,
            hint=hint,
        )

        return guess_obj
    except:
        return None