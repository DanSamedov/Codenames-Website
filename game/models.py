from django.db import models

# Create your models here.
class Word(models.Model):
    text = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.text


class Card(models.Model):
    words = models.JSONField(default=dict)
    game = models.ForeignKey('room.Game', on_delete=models.CASCADE)

    def __str__(self):
        return f"Game {self.game.id} - {len(self.words)} words"


def default_hints():
    return {
        "Red": [],
        "Blue": []
    }


class Hint(models.Model):
    game = models.ForeignKey('room.Game', on_delete=models.CASCADE)
    hints = models.JSONField(default=default_hints)
