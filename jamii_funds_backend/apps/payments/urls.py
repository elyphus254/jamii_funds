from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MpesaTransactionViewSet, mpesa_callback

router = DefaultRouter()
router.register(r"transactions", MpesaTransactionViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("c2b/", mpesa_callback, name="c2b"),
]