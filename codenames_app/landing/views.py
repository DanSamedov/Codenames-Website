from django.shortcuts import render
from room.models import Game, Player
from .forms import CreateRoomForm, JoinRoomForm
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
