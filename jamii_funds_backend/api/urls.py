# api/urls.py
"""
API URL configuration.

Public endpoints:
    POST  /auth/register/        → create a user + return JWT
    POST  /auth/login/           → obtain JWT pair
    POST  /auth/token/refresh/   → refresh access token

Protected endpoints (all ViewSets):
    /chamas/
    /members/
    /contributions/
    /loans/
    /interests/
    /profit-distributions/
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

# ----------------------------------------------------------------------
# 1. Import your ViewSets
# ----------------------------------------------------------------------
from .views import (
    ChamaViewSet,
    MemberViewSet,
    ContributionViewSet,
    LoanViewSet,
    InterestEntryViewSet,
    ProfitDistributionViewSet,
    register,          # <-- your custom register view
)

# ----------------------------------------------------------------------
# 2. Router for protected resources
# ----------------------------------------------------------------------
router = DefaultRouter(trailing_slash=False)          # optional: remove trailing slash
router.register(r'chamas', ChamaViewSet, basename='chama')
router.register(r'members', MemberViewSet, basename='member')
router.register(r'contributions', ContributionViewSet, basename='contribution')
router.register(r'loans', LoanViewSet, basename='loan')
router.register(r'interests', InterestEntryViewSet, basename='interest')
router.register(r'profit-distributions', ProfitDistributionViewSet, basename='profitdistribution')

# ----------------------------------------------------------------------
# 3. URL patterns
# ----------------------------------------------------------------------
urlpatterns = [
    # ------------------------------------------------------------------
    # Public authentication endpoints
    # ------------------------------------------------------------------
    path('auth/register/', register, name='register'),                 # custom register
    path('auth/login/', TokenObtainPairView.as_view(), name='login'),  # JWT login
    path('auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    # ------------------------------------------------------------------
    # Protected API resources (all ViewSets)
    # ------------------------------------------------------------------
    path('', include(router.urls)),

    # ------------------------------------------------------------------
    # OPTIONAL: API documentation (uncomment after installing drf-spectacular)
    # ------------------------------------------------------------------
    # path('schema/', SpectacularAPIView.as_view(), name='schema'),
    # path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    # path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]