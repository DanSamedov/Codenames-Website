from django.shortcuts import render
from django.http import HttpResponse
from .models import Game, Player
from .forms import CreateRoomForm, JoinRoomForm, ChooseTeamForm
from django.shortcuts import get_object_or_404, redirect


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

    if request.method == 'POST':
        if "choose_team" in request.POST:
            choose_form = ChooseTeamForm(request.POST)
            if choose_form.is_valid():
                selected_team = choose_form.cleaned_data["team"]
                selected_role = choose_form.cleaned_data["role"]

                current_player.team = selected_team
                current_player.leader = selected_role
                current_player.save()
                
                choose_form = ChooseTeamForm()

        elif "start_game" in request.POST and current_player and current_player.creator:
            return redirect(f'/game/{game_obj.id}/')

    else:
        choose_form = ChooseTeamForm()
    
    context = {
        'choose_form': choose_form,
        'game_obj': game_obj,
        'player_obj': player_obj,
        'current_player' : current_player,
    }
    return render(request, 'setup_room.html', context)

# def setup_room_view(request, id):
#     # Initialize the form to display to the user
#     choose_form = ChooseTeamForm()

#     # Get the current game object
#     game_obj = get_object_or_404(Game, id=id)

#     # Get the players in the game
#     player_obj = Player.objects.filter(game=game_obj)

#     # Get the current player's details using the session
#     current_player_username = request.session.get("username")
#     current_player = Player.objects.filter(game=game_obj, username=current_player_username).first() if current_player_username else None

#     # Render the setup page without handling form submission via POST
#     context = {
#         'choose_form': choose_form,
#         'game_obj': game_obj,
#         'player_obj': player_obj,
#         'current_player': current_player,
#     }
#     return render(request, 'setup_room.html', context)

