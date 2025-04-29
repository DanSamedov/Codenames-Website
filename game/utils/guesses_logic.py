from game.models import Guess
from django.db import transaction


def add_guess(guess_ids, hint):
    if not hint:
        raise ValueError("Cannot create guesses without a valid hint")

    cleaned_words = [
        gid.replace('card-', '', 1)
        for gid in guess_ids
    ]

    guesses_to_create = [
        Guess(hint=hint, guess=word)
        for word in cleaned_words
    ]

    try:
        with transaction.atomic():
            return Guess.objects.bulk_create(guesses_to_create)
    except Exception as e:
        raise Exception(f"Failed to create guesses: {e}")

