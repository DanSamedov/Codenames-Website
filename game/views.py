from django.shortcuts import render, get_object_or_404
from .models import Card, Guess
from room.models import Game, Player
from game.utils.hints_logic import get_last_hint
from django.core.serializers.json import DjangoJSONEncoder
import json

# Create your views here.
def game_view(request, id):
    game_obj = get_object_or_404(Game, id=id)

    current_player_username = request.session.get("username")
    current_player = Player.objects.filter(game=game_obj, username=current_player_username).first() if current_player_username else None

    cards = Card.objects.filter(game=game_obj)
    cards_list = list(cards.values('word', 'color'))
    last_hint = get_last_hint(game_obj)
    picked_cards = Guess.objects.filter(hint__game=game_obj.id).values_list('guess', flat=True)
    
    context = {
        'game_obj': game_obj,
        'cards_list': cards_list,
        'current_player': current_player,
        'last_hint': last_hint,
        'picked_cards': picked_cards,
    }

    return render(request, 'game.html', context)
