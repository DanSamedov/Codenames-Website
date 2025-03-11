from django.urls import path 
from . import views

urlpatterns = [
    path('', views.landing_forms_view, name='landing'),
    path('<int:id>/', views.game_room_view, name='game_room'),
]