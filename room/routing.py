from django.urls import path
from .consumers import *

websocket_urlpatterns = [
    path("ws/room/<int:id>/", RoomConsumer.as_asgi())
]