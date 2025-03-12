from django.urls import path 
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('<int:id>/', views.game_view, name='game_room'),
]