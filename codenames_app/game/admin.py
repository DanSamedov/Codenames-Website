from django.contrib import admin
from .models import Word, Card, Hint

# Register your models here.
admin.site.register(Word)
admin.site.register(Card)
admin.site.register(Hint)
