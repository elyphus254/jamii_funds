# apps/api/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter

# Import your viewsets
from apps.chamas.views import ChamaViewSet
#from apps.contributions.views import ContributionViewSet
#from apps.payments.views import PaymentViewSet

router = DefaultRouter()
router.register(r'chamas', ChamaViewSet, basename='chama')
#router.register(r'contributions', ContributionViewSet, basename='contribution')
#router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
]