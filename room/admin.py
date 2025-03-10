from django.contrib import admin
from .models import Game, Player, Word, Card

# Register your models here.
admin.site.register(Game)
admin.site.register(Player)
admin.site.register(Word)
admin.site.register(Card)
