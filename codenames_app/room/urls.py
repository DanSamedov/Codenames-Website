from django.urls import path 
from . import views

urlpatterns = [
    path('<int:id>/', views.setup_room_view, name='room'),
]