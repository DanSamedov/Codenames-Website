from django.contrib import admin
from django.urls import path, include
from django.views.generic import TemplateView
from . import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('room/', include('room.urls')),
    path('', include('landing.urls')),
    path('game/', include('game.urls')),
    path("up/", views.health_check, name="health_check"),
]
