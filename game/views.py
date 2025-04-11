from django.shortcuts import render, get_object_or_404
from .models import Card, Hint
from room.models import Game, Player
from game.utils.hints_logic import get_last_hint

# Create your views here.
def game_view(request, id):
    game_obj = get_object_or_404(Game, id=id)

    current_player_username = request.session.get("username")
    current_player = Player.objects.filter(game=game_obj, username=current_player_username).first() if current_player_username else None

    card_obj = Card.objects.filter(game=game_obj)
    last_hint = get_last_hint(game_obj)

    context = {
        'game_obj': game_obj,
        'cards': card_obj,
        'current_player': current_player,
        'last_hint': last_hint
    }
    return render(request, 'game.html', context)
