from rest_framework.routers import DefaultRouter
from .views import *

router = DefaultRouter()
router.register(r'chamas', ChamaViewSet)
router.register(r'members', MemberViewSet)
router.register(r'contributions', ContributionViewSet)
router.register(r'loans', LoanViewSet)
router.register(r'interests', InterestEntryViewSet)
router.register(r'profit-distributions', ProfitDistributionViewSet)

urlpatterns = router.urls
