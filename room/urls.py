from django.urls import path 
from . import views

urlpatterns = [
    path('create/', views.create_room_view, name='create_room'),
    path('<int:id>/', views.game_room_view, name='game_room'),
    path('join/', views.join_room_view, name='join_room'),
]