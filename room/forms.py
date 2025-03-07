from django import forms
from .models import Player


class CreateRoomForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['username']


class JoinRoomForm(forms.Form):
    game_id = forms.IntegerField(label="Game ID", required=True)
    username = forms.CharField(label="Your Name", max_length=16, required=True)