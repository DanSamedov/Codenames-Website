from django.urls import path
from .consumers.consumers import GameConsumer

websocket_urlpatterns = [
    path("ws/game/<int:id>/", GameConsumer.as_asgi())
]