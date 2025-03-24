from django import forms

class ClueWordForm(forms.Form):
    clue = forms.CharField(label="Enter your name",
        max_length=32,
        required=True,
        widget=forms.TextInput(attrs={'placeholder': 'Enter your clue'}))