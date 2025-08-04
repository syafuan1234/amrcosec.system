from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse

# Temporary homepage to confirm Render is working
def home(request):
    return HttpResponse("✅ Your system is deployed and running!")

urlpatterns = [
    path('', home),                         # Show this on /
    path('admin/', admin.site.urls),        # Admin panel
    path('companies/', include('companies.urls')),  # Your app URLs
]
