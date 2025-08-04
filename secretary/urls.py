from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),                         # ✅ Admin panel
    path('', include('companies.urls')),                     # ✅ Your app views (Company, Director, etc.)
]
