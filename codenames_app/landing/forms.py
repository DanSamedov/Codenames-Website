from django import forms
from room.models import Player


class CreateRoomForm(forms.ModelForm):
    class Meta:
        model = Player
        fields = ['username']
        labels = {
            'username': "Enter your name"
        }
        widgets = {
            'username': forms.TextInput(attrs={
                'class': 'w-full p-4 border bg-transparent text-white placeholder-white text-base input-field-primary',
                'placeholder': 'Enter your name',
                'maxlength': '16',
                'minlength': '3'
            })
        }


class JoinRoomForm(forms.Form):
    username = forms.CharField(
        label="Enter your name",
        max_length=16,
        min_length=3,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'w-full p-4 border bg-transparent text-white placeholder-white text-base input-field-secondary',
            'placeholder': 'Enter your name'
        })
    )

    game_id = forms.IntegerField(
        label="Enter room id",
        required=True,
        widget=forms.NumberInput(attrs={
            'class': 'w-full p-4 border bg-transparent text-white placeholder-white text-base input-field-secondary',
            'placeholder': 'Enter room ID'
        })
    )
