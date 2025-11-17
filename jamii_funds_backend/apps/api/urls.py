from django.urls import path, include
from rest_framework.routers import DefaultRouter
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from apps.chamas.views import ChamaViewSet
from apps.contributions.views import ContributionViewSet

router = DefaultRouter()
router.register(r"chamas", ChamaViewSet)
router.register(r'contributions', ContributionViewSet, basename='contribution')

urlpatterns = [
    path("", include(router.urls)),
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
]