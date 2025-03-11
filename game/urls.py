from django.urls import path 
from . import views
from django.views.generic import TemplateView

urlpatterns = [
    path('<int:id>/', TemplateView.as_view(template_name='landing.html'), name='game_room'),
]