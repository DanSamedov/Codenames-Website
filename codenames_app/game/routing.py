from django.urls import path
from .consumers import *

websocket_urlpatterns = [
    path("ws/game/<int:id>/", GameConsumer.as_asgi())
]