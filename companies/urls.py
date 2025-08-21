from django.urls import path
from django.http import HttpResponse
from . import views
from .views import download_pdf

urlpatterns = [
    path('', lambda request: HttpResponse("✅ Welcome to AMRCOSEC System! Your system is running.")),
    path("generate-doc/<int:company_id>/", views.generate_company_doc, name="generate_company_doc"),
    path('generate-doc/<int:company_id>/<int:template_id>/', views.generate_company_doc, name='generate_company_doc'),
    path('choose-template/<int:company_id>/', views.choose_template, name='choose_template'),
    path('generate-doc/<int:company_id>/<int:template_id>/<str:director_id>/', views.generate_company_doc, name='generate_company_doc_with_director'),
    path('companies/<int:company_id>/template/<int:template_id>/pdf/', download_pdf, name='download_pdf'),

]
