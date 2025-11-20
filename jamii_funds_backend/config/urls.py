# config/urls.py

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django_tenants.utils import get_public_schema_name


def landing_page(request):
    if request.tenant.schema_name != get_public_schema_name():
        return HttpResponse("<h1>Your Chama Dashboard</h1>")
    return HttpResponse(
        "<h1>Jamii Funds – Welcome!</h1>"
        "<p><a href='/api/auth/register/'>Register Here</a></p>"
    )


urlpatterns = [
    path('', landing_page),

    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.auth_app.urls')),
    path('api-auth/', include('rest_framework.urls')),

    # THIS LINE MAKES /api/chamas/ WORK
    path('api/', include('apps.api.urls')),
]