from django.shortcuts import render, get_object_or_404
from .models import Card
from room.models import Game, Player
from .cards_logic import generate_cards

# Create your views here.
def game_view(request, id):
    game_obj = get_object_or_404(Game, id=id)

    current_player_username = request.session.get("username")
    current_player = Player.objects.filter(game=game_obj, username=current_player_username).first() if current_player_username else None

    if not Card.objects.filter(game=game_obj).exists() and current_player.creator:
        generate_cards(game_obj)

    card_obj = Card.objects.filter(game=game_obj)

    context = {
        'game_obj': game_obj,
        'cards': card_obj,
        'current_player': current_player,
    }
    return render(request, 'game.html', context)