# core/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F, Q
from decimal import Decimal
from django.db import models  


from .models import Chama, Member, Loan, Contribution
from .serializers import (
    ChamaSerializer, MemberSerializer, LoanSerializer,
    ContributionSerializer, LoanApplicationSerializer
)
from .permissions import IsChamaAdmin, IsMemberOfChama


# ==============================
# 1. CHAMA VIEWSET
# ==============================
class ChamaViewSet(viewsets.ModelViewSet):
    queryset = Chama.objects.all()
    serializer_class = ChamaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Chama.objects.all()
        # Regular users only see chamas they created or are members of
        return Chama.objects.filter(
            models.Q(created_by=user) | models.Q(members__user=user)
        ).distinct()

    def perform_create(self, serializer):
        # Auto-set creator
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsChamaAdmin])
    def add_member(self, request, pk=None):
        chama = self.get_object()
        user_id = request.data.get('user_id')
        if not user_id:
            return Response({'error': 'user_id required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = settings.AUTH_USER_MODEL.objects.get(id=user_id)
        except settings.AUTH_USER_MODEL.DoesNotExist:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

        member, created = Member.objects.get_or_create(
            user=user, chama=chama, defaults={'is_admin': False}
        )
        if created:
            return Response({'status': 'Member added'}, status=status.HTTP_201_CREATED)
        return Response({'status': 'Already a member'}, status=status.HTTP_200_OK)


# ==============================
# 2. MEMBER VIEWSET
# ==============================
class MemberViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Member.objects.all()
        # Only see members in your chamas
        return Member.objects.filter(chama__members__user=user).distinct()

    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user's membership profile"""
        membership = Member.objects.filter(user=request.user).first()
        if not membership:
            return Response({'error': 'Not a member of any chama'}, status=status.HTTP_404_NOT_FOUND)
        serializer = self.get_serializer(membership)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def dashboard(self, request):
        """Member dashboard: contributions, loans, balance"""
        member = Member.objects.filter(user=request.user).first()
        if not member:
            return Response({'error': 'Not in any chama'}, status=status.HTTP_404_NOT_FOUND)

        contributions = member.contributions.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')
        loans = member.loans.filter(status__in=['Approved', 'Pending'])
        outstanding = loans.aggregate(total=Sum('amount'))['total'] or Decimal('0.00')

        data = {
            'chama': member.chama.name,
            'total_contributed': contributions,
            'active_loans': LoanSerializer(loans, many=True).data,
            'outstanding_balance': outstanding,
            'can_apply_loan': contributions >= outstanding * 3  # 3x savings rule
        }
        return Response(data)


# ==============================
# 3. LOAN VIEWSET
# ==============================
class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.select_related('member__user', 'member__chama').all()
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Loan.objects.all()
        # Only see loans in your chama
        return Loan.objects.filter(member__chama__members__user=user)

    def get_serializer_class(self):
        if self.action == 'apply':
            return LoanApplicationSerializer
        return LoanSerializer

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def apply(self, request):
        """Custom loan application with eligibility check"""
        member = Member.objects.filter(user=request.user).first()
        if not member:
            return Response({'error': 'Not a member'}, status=status.HTTP_403_FORBIDDEN)

        serializer = LoanApplicationSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # Eligibility: 3x savings
            total_saved = member.contributions.aggregate(t=Sum('amount'))['t'] or Decimal('0.00')
            requested = serializer.validated_data['amount']
            if total_saved < requested * 3:
                return Response({
                    'error': 'Insufficient savings. Need 3x loan amount.',
                    'required': requested * 3,
                    'saved': total_saved
                }, status=status.HTTP_400_BAD_REQUEST)

            loan = serializer.save(member=member, status='Pending')
            return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'], permission_classes=[IsChamaAdmin])
    def approve(self, request, pk=None):
        loan = self.get_object()
        if loan.status != 'Pending':
            return Response({'error': 'Loan not pending'}, status=status.HTTP_400_BAD_REQUEST)

        loan.status = 'Approved'
        loan.approved_date = timezone.now()
        loan.save()
        return Response({'status': 'Loan approved'})

    @action(detail=True, methods=['post'], permission_classes=[IsChamaAdmin])
    def reject(self, request, pk=None):
        loan = self.get_object()
        loan.status = 'Rejected'
        loan.save()
        return Response({'status': 'Loan rejected'})