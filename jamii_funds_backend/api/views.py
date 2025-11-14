from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from core.models import *
from .serializers import *
from django.db.models import Sum
from decimal import Decimal

class ChamaViewSet(viewsets.ModelViewSet):
    queryset = Chama.objects.all()
    serializer_class = ChamaSerializer
    permission_classes = [permissions.IsAuthenticated]


class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer
    permission_classes = [permissions.IsAuthenticated]


class ContributionViewSet(viewsets.ModelViewSet):
    queryset = Contribution.objects.all()
    serializer_class = ContributionSerializer
    permission_classes = [permissions.IsAuthenticated]


class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer
    permission_classes = [permissions.IsAuthenticated]


class InterestEntryViewSet(viewsets.ModelViewSet):
    queryset = InterestEntry.objects.all()
    serializer_class = InterestEntrySerializer
    permission_classes = [permissions.IsAuthenticated]


class ProfitDistributionViewSet(viewsets.ModelViewSet):
    queryset = ProfitDistribution.objects.select_related('chama').all().order_by('-created_at')
    serializer_class = ProfitDistributionSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=["post"])
    def compute(self, request, pk=None):
        pd = self.get_object()
        if pd.computed:
            return Response({"detail": "Already computed"}, status=status.HTTP_400_BAD_REQUEST)

        entries = InterestEntry.objects.filter(
            loan__chama=pd.chama,
            recorded_at__date__gte=pd.period_start,
            recorded_at__date__lte=pd.period_end
        )
        total_interest = entries.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        pd.total_interest_collected = total_interest

        contributions = Contribution.objects.filter(
            chama=pd.chama, status='confirmed',
            created_at__date__gte=pd.period_start,
            created_at__date__lte=pd.period_end
        )
        total_contrib = contributions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')

        results = {}
        if total_contrib > 0:
            members = pd.chama.members.all()
            for m in members:
                member_sum = contributions.filter(member=m).aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
                share = (Decimal(member_sum) / Decimal(total_contrib)) * total_interest
                results[str(m.id)] = {
                    "member_id": m.member_id,
                    "member_name": m.person.username,
                    "contributed": str(member_sum),
                    "share": str(round(share, 2))
                }

        pd.results = results
        pd.computed = True
        pd.save()
        return Response({"message": "Profit distribution computed", "results": results})
