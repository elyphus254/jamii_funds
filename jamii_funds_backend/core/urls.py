from rest_framework.routers import DefaultRouter
from .views import ChamaViewSet, MemberViewSet, LoanViewSet

router = DefaultRouter()
router.register('chamas', ChamaViewSet)
router.register('members', MemberViewSet)
router.register('loans', LoanViewSet)

urlpatterns = router.urls
