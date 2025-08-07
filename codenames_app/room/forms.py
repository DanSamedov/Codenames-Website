from django import forms

class ChooseTeamForm(forms.Form):
    ROLE_CHOICES = [
        ('',    '--- Select role ---'),
        ('False','Operative'),
        ('True', 'Spymaster'),
    ]

    team = forms.CharField(widget=forms.HiddenInput(), required=True)

    role = forms.TypedChoiceField(
        choices=ROLE_CHOICES,
        coerce=lambda val: val == 'True',
        empty_value=None,
        required=True,
        error_messages={
            'required': 'You must choose either Operative or Spymaster.'
        },
        widget=forms.Select(attrs={
            'class': 'bg-[var(--accent-color)] border-[var(--text-dark)] rounded'
        })
    )
