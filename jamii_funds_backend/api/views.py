# api/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status, viewsets
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

from .models import (
    Chama, Member, Contribution, Loan, InterestEntry, ProfitDistribution, Membership
)
from .serializers import (
    ChamaSerializer, MemberSerializer, ContributionSerializer,
    LoanSerializer, InterestEntrySerializer, ProfitDistributionSerializer, MembershipSerializer
)

User = get_user_model()


# ------------------------------------------------------------------
# 1. PUBLIC: Register
# ------------------------------------------------------------------
@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    phone = request.data.get('phone')
    email = request.data.get('email', '')

    if not all([username, password, phone]):
        return Response({'error': 'username, password, phone required'}, status=400)

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username taken'}, status=400)

    user = User.objects.create_user(username=username, password=password, email=email)
    Member.objects.create(user=user, name=username, phone=phone, email=email)

    refresh = RefreshToken.for_user(user)
    return Response({
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {'id': user.id, 'username': user.username}
    }, status=201)


# ------------------------------------------------------------------
# 2. VIEWSETS (add only the ones you need now)
# ------------------------------------------------------------------
class ChamaViewSet(viewsets.ModelViewSet):
    queryset = Chama.objects.all()
    serializer_class = ChamaSerializer
    permission_classes = [AllowAny]  # tighten later

class MemberViewSet(viewsets.ModelViewSet):
    queryset = Member.objects.all()
    serializer_class = MemberSerializer

class ContributionViewSet(viewsets.ModelViewSet):
    queryset = Contribution.objects.all()
    serializer_class = ContributionSerializer

class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.all()
    serializer_class = LoanSerializer

class InterestEntryViewSet(viewsets.ModelViewSet):
    queryset = InterestEntry.objects.all()
    serializer_class = InterestEntrySerializer

class ProfitDistributionViewSet(viewsets.ModelViewSet):
    queryset = ProfitDistribution.objects.all()
    serializer_class = ProfitDistributionSerializer

class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.all()
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]    