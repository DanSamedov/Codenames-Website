from django import forms

class ChooseTeamForm(forms.Form):
    ROLE_CHOICES = [
        ('',    '--- Select role ---'),
        ('False','Guesser'),
        ('True', 'Leader'),
    ]

    team = forms.CharField(widget=forms.HiddenInput(), required=True)

    role = forms.TypedChoiceField(
        choices=ROLE_CHOICES,
        coerce=lambda val: val == 'True',
        empty_value=None,
        required=True,
        error_messages={
            'required': 'You must choose either Guesser or Leader.'
        },
        widget=forms.Select(attrs={
            'class': 'bg-[var(--accent-color)] border-[var(--text-dark)] rounded'
        })
    )
