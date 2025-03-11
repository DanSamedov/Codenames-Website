import random
from room.models import Card, Word

def generate_cards(game):
    words = list(Word.objects.order_by('?')[:25])
    colors = ['Red'] * 8 + ['Blue'] * 8 + ['Neutral'] * 7 + ['Black']
    random.shuffle(colors)

    word_dict = {word.text: color for word, color in zip(words, colors)}

    Card.objects.filter(game=game).delete()
    Card.objects.create(game=game, words=word_dict)