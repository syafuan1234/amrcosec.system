from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('companies.urls')),  # ✅ this is the correct app name
]
