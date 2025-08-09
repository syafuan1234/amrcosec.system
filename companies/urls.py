from django.urls import path
from django.http import HttpResponse
from . import views

urlpatterns = [
    path('', lambda request: HttpResponse("✅ Welcome to AMRCOSEC System! Your system is running.")),
    path('directors/add/', views.add_director, name='add_director'),
    path("generate-doc/<int:company_id>/", views.generate_company_doc, name="generate_company_doc"),
]
