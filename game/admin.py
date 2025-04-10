from django.contrib import admin
from .models import Word, Card, Hint, Guess

# Register your models here.
admin.site.register(Word)
admin.site.register(Card)
admin.site.register(Hint)
admin.site.register(Guess)