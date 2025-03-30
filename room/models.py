from django.db import models

# Create your models here.
def team_choices():
    return [
            ('None', 'None'),
            ('Blue', 'Blue Team'),
            ('Red', 'Red Team'),
        ]


class Game(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    starting_team = models.CharField(max_length=10, choices=team_choices(), default='None')
    winners = models.CharField(max_length=4, choices=[("Blue", "Blue"), ("Red", "Red"), ("Draw", "Draw")], null=True, blank=True)


class Player(models.Model):
    username = models.CharField(default='', max_length=16)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    creator = models.BooleanField(default=False)
    leader = models.BooleanField(default=False)
    ready = models.BooleanField(default=False)
    team = models.CharField(
        max_length=10,
        choices=team_choices(),
        default='None'
    )

    class Meta:
        unique_together = ('username', 'game')