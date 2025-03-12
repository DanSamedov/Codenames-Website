from django.shortcuts import render, get_object_or_404
from .models import Card
from room.models import Game
from .cards_logic import generate_cards

# Create your views here.
def game_view(request, id):
    game_obj = get_object_or_404(Game, id=id)

    if not Card.objects.filter(game=game_obj).exists():
        generate_cards(game_obj)

    card_obj = Card.objects.filter(game=game_obj)

    context = {
        'game_obj': game_obj,
        'cards': card_obj,
    }
    return render(request, 'game.html', context)