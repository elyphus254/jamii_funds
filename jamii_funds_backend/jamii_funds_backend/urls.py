# jamii_funds_backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


def home(request):
    """Friendly landing page for the backend."""
    return HttpResponse("""
    <h1 style="color: #00A651; font-family: system-ui;">Jamii Funds Backend</h1>
    <p>API is live! Visit:</p>
    <ul style="font-family: system-ui;">
        <li><a href="/admin/">Admin Panel</a></li>
        <li><a href="/api/">API Endpoints</a></li>
        <li><a href="/auth/">Authentication</a></li>
        <li><a href="/api/docs/">Swagger UI</a></li>
        <li><a href="/api/redoc/">Redoc Docs</a></li>
    </ul>
    <hr>
    <small>Built with Django + DRF | Kenya</small>
    """)


urlpatterns = [
    # ------------------------------------------------------------------
    # 1. Root & Docs
    # ------------------------------------------------------------------
    path('', home, name='home'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    # ------------------------------------------------------------------
    # 2. Apps
    # ------------------------------------------------------------------
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),        # ← Your Chama API
    path('auth/', include('auth_app.urls')),  # ← Login, Register, JWT

    # ------------------------------------------------------------------
    # 3. Health Check (optional, for uptime monitors)
    # ------------------------------------------------------------------
    path('health/', lambda r: HttpResponse("OK", status=200), name='health'),
]

# ------------------------------------------------------------------
# 4. Media in Development Only
# ------------------------------------------------------------------
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)