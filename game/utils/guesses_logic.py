from game.models import Guess, Hint
from room.models import Game
from django.db import transaction

def add_guess(guesses, hint):
    if not hint:
        raise ValueError("Cannot create guesses without a valid hint")
    
    guesses_to_create = [
        Guess(hint=hint, guess=guess)
        for guess in guesses]

    try:
        with transaction.atomic():
            return Guess.objects.bulk_create(guesses_to_create)
    except Exception as e:
        raise Exception(f"Failed to create guesses: {str(e)}")
