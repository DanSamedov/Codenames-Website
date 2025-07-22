from django import forms


class ChooseTeamForm(forms.Form):
    TEAM_CHOICE = [
        ('Blue', 'Team Blue'),
        ('Red', 'Team Red')
    ]

    ROLE_CHOICE = [
        (True, 'Leader'),
        (False, 'Guesser')
    ]

    team = forms.ChoiceField(choices=TEAM_CHOICE, widget=forms.RadioSelect, required=False)
    role = forms.ChoiceField(choices=ROLE_CHOICE, widget=forms.RadioSelect, required=False)