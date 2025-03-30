import random
from game.models import Card, Word
from room.models import Game

def generate_cards(game):
    starting_team = random.choice(('Red', 'Blue'))

    words = list(Word.objects.order_by('?')[:25])
    if starting_team == 'Red':
        colors = ['Red'] * 9 + ['Blue'] * 8 + ['Neutral'] * 7 + ['Black']
    else:
        colors = ['Red'] * 8 + ['Blue'] * 9 + ['Neutral'] * 7 + ['Black']

    random.shuffle(colors)

    word_list = [{'word': word.text, 'color': color} for word, color in zip(words, colors)]

    Card.objects.filter(game=game).delete()
    Card.objects.create(game=game, words=word_list)

    game.starting_team = starting_team
    game.save()