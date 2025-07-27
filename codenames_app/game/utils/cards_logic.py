import random
from game.models import Card, Word
from game.consumers.constants import TEAM_RED, TEAM_BLUE, TEAM_NEUTRAL, TEAM_ASSASSIN
from typing import Any


def generate_cards(game: Any) -> None:
    starting_team = random.choice((TEAM_RED, TEAM_BLUE))
    words = list(Word.objects.order_by('?')[:25])
    
    if starting_team == TEAM_RED:
        colors = [TEAM_RED] * 9 + [TEAM_BLUE] * 8 + [TEAM_NEUTRAL] * 7 + [TEAM_ASSASSIN]
    else:
        colors = [TEAM_BLUE] * 9 + [TEAM_RED] * 8 + [TEAM_NEUTRAL] * 7 + [TEAM_ASSASSIN]
    random.shuffle(colors)
    
    Card.objects.filter(game=game).delete()
    cards_to_create = [
        Card(
            game=game,
            word=word.text,
            color=color
        )
        for word, color in zip(words, colors)
    ]
    Card.objects.bulk_create(cards_to_create)
    
    game.starting_team = starting_team
    game.save()