# api/views.py
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.db import transaction
from django.db.models import Sum
from django.shortcuts import get_object_or_404
from django.utils import timezone

from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.exceptions import ValidationError
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.views import APIView

from .models import (
    Chama,
    Member,
    Membership,
    Contribution,
    Loan,
    Repayment,
    MpesaTransaction,
)
from .serializers import (
    ChamaSerializer,
    MemberSerializer,
    MembershipSerializer,
    ContributionSerializer,
    LoanSerializer,
    LoanApplicationSerializer,
    MpesaCallbackSerializer,
    RepaymentSerializer,
    MpesaTransactionSerializer,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


# ----------------------------------------------------------------------
# Helper: Get Member from User
# ----------------------------------------------------------------------
def get_member_from_user(user: "AbstractUser") -> Member:
    """Return Member linked to the authenticated User."""
    return get_object_or_404(Member, user=user)


# ----------------------------------------------------------------------
# 1. CHAMA VIEWSET
# ----------------------------------------------------------------------
@extend_schema(tags=["Chama"])
class ChamaViewSet(viewsets.ModelViewSet):
    queryset = Chama.objects.select_related().all()
    serializer_class = ChamaSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "description"]
    ordering_fields = ["created_at", "name"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(
            memberships__member__user=user,
            memberships__is_active=True,
        ).distinct()


# ----------------------------------------------------------------------
# 2. MEMBER VIEWSET (Read-only for user)
# ----------------------------------------------------------------------
@extend_schema(tags=["Member"])
class MemberViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = MemberSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return Member.objects.select_related("user").all()
        return Member.objects.filter(user=user)


# ----------------------------------------------------------------------
# 3. MEMBERSHIP VIEWSET – Join / Leave Chama
# ----------------------------------------------------------------------
@extend_schema(tags=["Membership"])
class MembershipViewSet(viewsets.ModelViewSet):
    queryset = Membership.objects.select_related("member__user", "chama")
    serializer_class = MembershipSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(member__user=user)

    @extend_schema(description="Join a chama (member must be active)")
    def perform_create(self, serializer):
        member = serializer.validated_data["member"]
        if not member.is_active:
            raise ValidationError("Cannot join with an inactive member.")
        serializer.save()


# ----------------------------------------------------------------------
# 4. CONTRIBUTION VIEWSET
# ----------------------------------------------------------------------
@extend_schema(tags=["Contribution"])
class ContributionViewSet(viewsets.ModelViewSet):
    queryset = Contribution.objects.select_related(
        "membership__member__user", "membership__chama"
    )
    serializer_class = ContributionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["confirmed", "membership__chama"]
    ordering_fields = ["date"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(membership__member__user=user)

    @transaction.atomic
    def perform_create(self, serializer):
        serializer.save(confirmed=False)

    @extend_schema(description="Get total confirmed contributions")
    @action(detail=False, methods=["get"])
    def my_summary(self, request):
        total = (
            self.get_queryset()
            .filter(confirmed=True)
            .aggregate(total=Sum("amount"))["total"]
            or Decimal("0.00")
        )
        return Response({"total_contributed": float(total)})


# ----------------------------------------------------------------------
# 5. LOAN VIEWSET – Apply, Approve, Reject
# ----------------------------------------------------------------------
@extend_schema(tags=["Loan"])
class LoanViewSet(viewsets.ModelViewSet):
    queryset = Loan.objects.select_related(
        "membership__member__user", "membership__chama"
    )
    serializer_class = LoanSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "membership__chama"]
    search_fields = ["membership__member__name"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(membership__member__user=user)

    def get_serializer_class(self):
        if self.action == "apply":
            return LoanApplicationSerializer
        return LoanSerializer

    @extend_schema(
        description="Apply for a loan (must have 3× savings)",
        request=LoanApplicationSerializer,
        responses={201: LoanSerializer}
    )
    @action(detail=False, methods=["post"])
    def apply(self, request):
        member = get_member_from_user(request.user)
        serializer = LoanApplicationSerializer(data=request.data, context={"request": request})
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        principal = serializer.validated_data["principal"]
        total_saved = member.memberships.filter(is_active=True).first().contributions.filter(confirmed=True).aggregate(t=Sum("amount"))["t"] or Decimal("0.00")

        if total_saved < principal * Decimal("3"):
            return Response({
                "error": "Insufficient savings",
                "required": float(principal * 3),
                "saved": float(total_saved),
            }, status=status.HTTP_400_BAD_REQUEST)

        membership = member.memberships.filter(is_active=True).first()
        if not membership:
            return Response({"error": "Not in any active chama"}, status=status.HTTP_403_FORBIDDEN)

        with transaction.atomic():
            loan = serializer.save(
                membership=membership,
                status=Loan.STATUS_PENDING,
            )
        return Response(LoanSerializer(loan).data, status=status.HTTP_201_CREATED)

    @extend_schema(description="Approve loan (admin only)")
    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def approve(self, request, pk=None):
        loan = self.get_object()
        if loan.status != Loan.STATUS_PENDING:
            return Response(
                {"detail": "Only pending loans can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            with transaction.atomic():
                loan.approve()
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response(LoanSerializer(loan).data)

    @extend_schema(description="Reject loan (admin only)")
    @action(detail=True, methods=["post"], permission_classes=[IsAdminUser])
    def reject(self, request, pk=None):
        loan = self.get_object()
        if loan.status != Loan.STATUS_PENDING:
            return Response(
                {"detail": "Only pending loans can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        loan.status = Loan.STATUS_REJECTED
        loan.save(update_fields=["status"])
        return Response(LoanSerializer(loan).data)


# ----------------------------------------------------------------------
# 6. REPAYMENT VIEWSET
# ----------------------------------------------------------------------
@extend_schema(tags=["Repayment"])
class RepaymentViewSet(viewsets.ModelViewSet):
    queryset = Repayment.objects.select_related(
        "loan__membership__member__user", "loan__membership__chama"
    )
    serializer_class = RepaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        return self.queryset.filter(loan__membership__member__user=user)

    @transaction.atomic
    def perform_create(self, serializer):
        repayment = serializer.save()
        repayment.loan.refresh_from_db()


# ----------------------------------------------------------------------
# 7. M-PESA TRANSACTION VIEWSET
# ----------------------------------------------------------------------
@extend_schema(tags=["M-Pesa"])
class MpesaTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = MpesaTransaction.objects.all()
    serializer_class = MpesaTransactionSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["status", "transaction_type"]
    ordering_fields = ["created_at"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return self.queryset
        member = Member.objects.filter(user=user).first()
        if member:
            return self.queryset.filter(phone=member.phone)
        return self.queryset.none()


class MpesaCallbackView(APIView):
    """
    M-Pesa C2B Confirmation URL (no auth required)
    Receives STK Push callback from Safaricom
    """
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        serializer = MpesaCallbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        body = serializer.validated_data["Body"]["stkCallback"]

        # Handle failure
        if body["ResultCode"] != 0:
            MpesaTransaction.objects.create(
                phone="",
                amount=0,
                transaction_type="unknown",
                checkout_request_id=body.get("CheckoutRequestID", ""),
                status="Failed",
                raw_callback=request.data
            )
            return Response({"status": "failed"}, status=200)

        # Extract metadata
        meta = {item["Name"]: item["Value"] for item in body["CallbackMetadata"]["Item"]}
        amount = Decimal(str(meta["Amount"]))
        receipt = meta["MpesaReceiptNumber"]
        phone = str(meta["PhoneNumber"])
        checkout_id = body["CheckoutRequestID"]

        # Record or update transaction
        mpesa_tx, created = MpesaTransaction.objects.get_or_create(
            checkout_request_id=checkout_id,
            defaults={
                "phone": phone,
                "amount": amount,
                "transaction_type": "contribution",  # default
                "mpesa_receipt": receipt,
                "status": "Completed",
                "raw_callback": request.data
            }
        )

        if not created:
            mpesa_tx.mpesa_receipt = receipt
            mpesa_tx.status = "Completed"
            mpesa_tx.save()

        # Auto-match contribution or repayment
        with transaction.atomic():
            membership = Membership.objects.filter(member__phone=phone).first()
            if not membership:
                return Response({"error": "Member not found"}, status=400)

            # Try to match contribution
            if mpesa_tx.transaction_type == "contribution":
                contrib = Contribution.objects.filter(
                    membership=membership,
                    amount=amount,
                    confirmed=False
                ).first()
                if contrib:
                    contrib.confirmed = True
                    contrib.transaction_ref = receipt
                    contrib.save()

            # Try to match repayment
            elif mpesa_tx.transaction_type == "repayment":
                loan = Loan.objects.filter(
                    membership=membership,
                    status="Approved",
                    balance_due__gte=amount
                ).first()
                if loan:
                    Repayment.objects.create(
                        loan=loan,
                        amount=amount,
                        transaction_ref=receipt
                    )

        return Response({"status": "success"}, status=200)