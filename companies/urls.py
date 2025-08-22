from django.urls import path
from django.http import HttpResponse
from . import views

urlpatterns = [
    path('', lambda request: HttpResponse("✅ Welcome to AMRCOSEC System! Your system is running.")),
    path("generate-doc/<int:company_id>/", views.generate_company_doc, name="generate_company_doc"),
    path('generate-doc/<int:company_id>/<int:template_id>/', views.generate_company_doc, name='generate_company_doc'),
    path('choose-template/<int:company_id>/', views.choose_template, name='choose_template'),
    path('generate-doc/<int:company_id>/<int:template_id>/<str:director_id>/', views.generate_company_doc, name='generate_company_doc_with_director'),
]
