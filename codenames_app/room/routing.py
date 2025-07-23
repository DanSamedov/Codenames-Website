from django.urls import path
from .consumers.consumers import RoomConsumer

websocket_urlpatterns = [
    path("ws/room/<int:id>/", RoomConsumer.as_asgi())
]