from django.db import models

# Create your models here.
class Game(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class Player(models.Model):
    TEAM_CHOICES = [
            ('None', 'No Team'),
            ('Blue', 'Blue Team'),
            ('Red', 'Red Team'),
        ]
        
    username = models.CharField(default='', max_length=16)
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    creator = models.BooleanField(default=False)
    leader = models.BooleanField(default=False)
    team = models.CharField(
        max_length=10,
        choices=TEAM_CHOICES,
        default='None'
    )


class Card(models.Model):
    COLOR_CHOICES = [
        ('Red', 'Red'),
        ('Blue', 'Blue'),
        ('Neutral', 'Neutral'),
        ('Black', 'Black')
    ]

    word = models.CharField(default='', unique=True)
    color = models.CharField(choices=COLOR_CHOICES, default='Neutral')

    def __str__(self):
        return self.text