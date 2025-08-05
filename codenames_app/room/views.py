from django.shortcuts import render
from .models import Game, Player
from game.models import Card
from .forms import ChooseTeamForm
from django.shortcuts import get_object_or_404


def setup_room_view(request, id):
    choose_form = ChooseTeamForm()

    game_obj = get_object_or_404(Game, id=id)
    player_obj = Player.objects.filter(game=game_obj)

    current_player_username = request.session.get("username")
    current_player = Player.objects.filter(game=game_obj, username=current_player_username).first() if current_player_username else None

    context = {
        'choose_form': choose_form,
        'game_obj': game_obj,
        'player_obj': player_obj,
        'current_player' : current_player,
    }
    # return render(request, 'room.html', context)
    return render(request, 'test.html', context)
