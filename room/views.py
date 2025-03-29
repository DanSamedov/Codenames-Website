from django.shortcuts import render
from .models import Game, Player
from game.models import Card
from .forms import CreateRoomForm, JoinRoomForm, ChooseTeamForm
from django.shortcuts import get_object_or_404, redirect
from game.utils.cards_logic import generate_cards


def landing_forms_view(request):
    create_form = CreateRoomForm()
    join_form = JoinRoomForm()

    if request.method == 'POST':
        username = request.POST.get("username")

        if username:
            request.session["username"] = username 

        if 'create_room' in request.POST:
            create_form = CreateRoomForm(request.POST)
            if create_form.is_valid():
                game_obj = Game.objects.create()

                player = create_form.save(commit=False)
                player.game = game_obj
                player.creator = True
                player.save()

                return redirect(f'/room/{game_obj.id}/')
        
        elif 'join_room' in request.POST:
            join_form = JoinRoomForm(request.POST)
            if join_form.is_valid():
                username = join_form.cleaned_data['username']
                game_id = join_form.cleaned_data['game_id']

                game_obj = get_object_or_404(Game, id=game_id)
                Player.objects.create(username=username, game=game_obj)

                return redirect(f'/room/{game_obj.id}/') 
            
    context = {
        'create_form': create_form,
        'join_form': join_form
    }

    return render(request, 'landing.html', context)


def setup_room_view(request, id):
    choose_form = ChooseTeamForm()

    game_obj = get_object_or_404(Game, id=id)
    player_obj = Player.objects.filter(game=game_obj)

    current_player_username = request.session.get("username")
    current_player = Player.objects.filter(game=game_obj, username=current_player_username).first() if current_player_username else None

    if not Card.objects.filter(game=game_obj).exists() and current_player.creator:
        generate_cards(game_obj)

    context = {
        'choose_form': choose_form,
        'game_obj': game_obj,
        'player_obj': player_obj,
        'current_player' : current_player,
    }
    return render(request, 'setup_room.html', context)
