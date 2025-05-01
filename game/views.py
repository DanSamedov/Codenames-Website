from django.shortcuts import render, get_object_or_404
from .models import Card
from room.models import Game, Player
from game.utils.hints_logic import get_last_hint

# Create your views here.
def game_view(request, id):
    game_obj = get_object_or_404(Game, id=id)

    current_player_username = request.session.get("username")
    current_player = Player.objects.filter(game=game_obj, username=current_player_username).first() if current_player_username else None

    cards = Card.objects.filter(game=game_obj)
    cards_list = list(cards.values('word', 'color'))
    last_hint = get_last_hint(game_obj)
    guessed_cards = Card.objects.filter(game=game_obj, is_guessed=True).values_list('word', flat=True)

    context = {
        'game_obj': game_obj,
        'cards_list': cards_list,
        'current_player': current_player,
        'last_hint': last_hint,
        'guessed_cards': guessed_cards,
    }

    return render(request, 'game.html', context)
