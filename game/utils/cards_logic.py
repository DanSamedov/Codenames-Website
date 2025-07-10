import random
from game.models import Card, Word


def generate_cards(game):
    starting_team = random.choice(('Red', 'Blue'))
    words = list(Word.objects.order_by('?')[:25])
    
    if starting_team == 'Red':
        colors = ['Red'] * 9 + ['Blue'] * 8 + ['Neutral'] * 7 + ['Black']
    else:
        colors = ['Blue'] * 9 + ['Red'] * 8 + ['Neutral'] * 7 + ['Black']
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