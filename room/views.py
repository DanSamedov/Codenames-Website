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
                game = Game.objects.create()

                player = create_form.save(commit=False)
                player.game = game
                player.creator = True
                player.save()

                return redirect(f'/room/{game.id}/')
        
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


def game_room_view(request, id):
    game_obj = get_object_or_404(Game, id=id)
    player_obj = Player.objects.filter(game=game_obj)

    current_player_username = request.session.get("username")
    current_player = Player.objects.filter(game=game_obj, username=current_player_username).first() if current_player_username else None

    if request.method == 'POST':
        form = ChooseTeamForm(request.POST)
        if form.is_valid():
            selected_team = form.cleaned_data["team"]
            selected_role = form.cleaned_data["role"]

            current_player.team = selected_team
            current_player.leader = selected_role
            
            form = ChooseTeamForm()
    else:
        form = ChooseTeamForm()
    
    context = {
        'form': form,
        'game_object': game_obj,
        'player_object': player_obj,
        'current_player' : current_player
    }
    return render(request, 'game_room.html', context)


# def choose_team_view(request):
#     if request.method == 'POST':
#         form = ChooseTeamForm(request.POST)
#         if form.is_valid():
#             selected_team = form.cleaned_data["team"]
#             selected_role = form.cleaned_data["role"]
#             print(f"User chose team: {selected_team}, role: {selected_role}")
#     else:
#         form = ChooseTeamForm()

#     context = {
#         'form': form
#     }

#     return render(request, 'game_room.html', context)


# def create_room_view(request):
#     form = CreateRoomForm(request.POST or None)
#     if request.method == 'POST' and form.is_valid():
#         game = Game.objects.create()

#         player = form.save(commit=False)
#         player.game = game
#         player.creator = True
#         player.save()

#         username = request.POST.get("username")

#         if username:
#             request.session["username"] = username 
        
#         return redirect(f'/room/{game.id}/')

#     context = {
#         'create_form': form
#     }
#     return render(request, 'landing.html', context)


# def join_room_view(request):
#     if request.method == 'POST':
#         form = JoinRoomForm(request.POST)
#         if form.is_valid():
#             game_id = form.cleaned_data['game_id']
#             username = form.cleaned_data['username']
            
#             game_obj = get_object_or_404(Game, id=game_id)
            
#             Player.objects.create(username=username, game=game_obj)

#             return redirect(f'/room/{game_obj.id}/')
#     else:
#         form = JoinRoomForm()
    
#     context = {
#         'form': form
#     }

#     return render(request, 'landing.html', context)