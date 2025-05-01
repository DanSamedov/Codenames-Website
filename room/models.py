from django.db import models
from game.models import Guess

# Create your models here.
def team_choices():
    return [
            ('None', 'None'),
            ('Blue', 'Blue'),
            ('Red', 'Red'),
        ]


class Game(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    starting_team = models.CharField(max_length=10, choices=team_choices(), default='None')
    winners = models.CharField(max_length=4, choices=[("Blue", "Blue"), ("Red", "Red"), ("Draw", "Draw")], null=True, blank=True)
    red_team_score = models.IntegerField(default=0)
    blue_team_score = models.IntegerField(default=0)

    def tally_scores(self):
        guesses = Guess.objects.filter(hint__game=self)
        red_guesses  = guesses.filter(hint__team="Red").count()
        blue_guesses = guesses.filter(hint__team="Blue").count()

        self.red_team_score  = red_guesses
        self.blue_team_score = blue_guesses
        self.save(update_fields=['red_team_score', 'blue_team_score'])
        
        return red_guesses, blue_guesses, self.starting_team


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