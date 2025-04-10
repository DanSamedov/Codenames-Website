from game.models import Guess
from room.models import Game

def add_guess(game_id, guess, team, hint_id):
    game = Game.objects.get(id=game_id)

    guess_obj, created = Guess.objects.get_or_create(
        game=game,
        team=team,
        defaults={'guess': []}
    )
    
    new_guess_entry = {
        "guess": guess,
        "hint_id": hint_id,
        # "correct": correct
    }
    
    guess_obj.guess.append(new_guess_entry)
    
    guess_obj.save()
    
    return guess_obj
