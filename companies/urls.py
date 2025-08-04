from django.urls import path
from . import views

urlpatterns = [
    path('directors/add/', views.add_director, name='add_director'),
]
