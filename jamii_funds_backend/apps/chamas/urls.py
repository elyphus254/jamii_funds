from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChamaViewSet

router = DefaultRouter()
router.register(r"", ChamaViewSet)

urlpatterns = [path("", include(router.urls))]