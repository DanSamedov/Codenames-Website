from django.db import models
from django.utils import timezone

# Create your models here.
class Word(models.Model):
    text = models.CharField(max_length=50, unique=True)

    def __str__(self):
        return self.text


class Card(models.Model):
    game = models.ForeignKey('room.Game', on_delete=models.CASCADE)
    word = models.CharField(max_length=255, null=True, blank=True, default="")
    color = models.CharField(max_length=255, null=True, blank=True, default="")
    is_guessed  = models.BooleanField(default=False)

    def __str__(self):
        return f"Game {self.game.id} - {self.word}"


class Hint(models.Model):
    game = models.ForeignKey('room.Game', on_delete=models.CASCADE)
    team = models.CharField(max_length=4, choices=[("Blue", "Blue"), ("Red", "Red")])
    word = models.CharField(max_length=255)
    num = models.CharField(max_length=255)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['game', 'team', '-created_at']),
        ]

    def __str__(self):
        return f"{self.team} team hint: {self.word} (Game {self.game.id})"
