from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ContributionViewSet

router = DefaultRouter()
router.register(r'', ContributionViewSet)

urlpatterns = [
    path('', include(router.urls)),
]