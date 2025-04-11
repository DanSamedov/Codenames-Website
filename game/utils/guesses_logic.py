from game.models import Guess, Hint
from room.models import Game

def add_guess(game_id, guess, team, clue_id):
    game = Game.objects.get(id=game_id)
    hint = Hint.objects.get(game=game)

    if clue_id != None:
        guess_obj = Guess.objects.create(
            game=game,
            team=team,
            guess=guess,
            hint=hint,
            clue_id=clue_id
        )

        return guess_obj
