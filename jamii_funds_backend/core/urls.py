from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'chamas', views.ChamaViewSet)
router.register(r'members', views.MemberViewSet)
router.register(r'loans', views.LoanViewSet)

urlpatterns = [
    path('', include(router.urls)),
]