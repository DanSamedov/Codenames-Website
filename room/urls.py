from django.urls import path 
from . import views

urlpatterns = [
    path('', views.landing_forms_view, name='landing'),
    path('<int:id>/', views.setup_room_view, name='setup_room'),
]