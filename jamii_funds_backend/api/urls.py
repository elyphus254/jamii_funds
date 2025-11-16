# api/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from . import views

# ------------------------------------------------------------------
# 1. API ROUTER
# ------------------------------------------------------------------
router = DefaultRouter()
router.register(r'chamas', views.ChamaViewSet, basename='chama')
router.register(r'members', views.MemberViewSet, basename='member')
router.register(r'memberships', views.MembershipViewSet, basename='membership')
router.register(r'contributions', views.ContributionViewSet, basename='contribution')
router.register(r'loans', views.LoanViewSet, basename='loan')
router.register(r'repayments', views.RepaymentViewSet, basename='repayment')
router.register(r'mpesa-transactions', views.MpesaTransactionViewSet, basename='mpesa-transaction')

# ------------------------------------------------------------------
# 2. URL PATTERNS
# ------------------------------------------------------------------
urlpatterns = [
    # API Endpoints
    path('', include(router.urls)),

    # M-Pesa C2B Confirmation URL (no auth)
    path('mpesa/c2b/', views.MpesaCallbackView.as_view(), name='mpesa-c2b'),

    # ------------------------------------------------------------------
    # 3. OpenAPI Schema & Docs
    # ------------------------------------------------------------------
    path('schema/', SpectacularAPIView.as_view(), name='schema'),
    path('docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]