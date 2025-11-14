from django.contrib import admin
from core import views 
from django.urls import path, include
from django.http import JsonResponse

def home(request):
    return JsonResponse({"message": "Welcome to Jamii Funds API"})

urlpatterns = [

    path('', home),
    
    path('admin/', admin.site.urls),

    # Authentication
    path('api/auth/', include('auth_app.urls')),

    # Core endpoints (chamas, members, loans, etc.)
    path('api/core/', include('core.urls')),

    # M-Pesa endpoints (Daraja integration)
    path('api/mpesa/', include('core.mpesa_urls')),
    #auth endpoints
    path('api/auth/', include('auth_app.urls')),
    
]

