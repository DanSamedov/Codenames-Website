from game.models import Guess

def add_guess(game, hint, word, clue_id, correct):
    guess_obj, created = Guess.objects.get_or_create(
        game=game,
        hint=hint,
        defaults={'guess': []}
    )
    
    new_guess_entry = {
        "word": word,
        "clue_id": clue_id,
        "correct": correct
    }
    
    guess_obj.guess.append(new_guess_entry)
    
    guess_obj.save()
    
    return guess_obj

