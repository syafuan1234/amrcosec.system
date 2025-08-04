from django.urls import path
from . import views
from django.http import HttpResponse

urlpatterns = [
    path('', lambda request: HttpResponse("✅ Welcome to AMRCOSEC System! Your system is running.")),
    path('directors/add/', views.add_director, name='add_director'),
]
