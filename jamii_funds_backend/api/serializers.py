# api/serializers.py
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING, Any

from django.db.models import Sum
from rest_framework import serializers
from drf_spectacular.utils import extend_schema_field, OpenApiTypes

from .models import (
    Chama,
    Member,
    Membership,
    Contribution,
    Loan,
    Repayment,
    MpesaTransaction,
)

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


# ----------------------------------------------------------------------
# 1. CHAMA
# ----------------------------------------------------------------------
@extend_schema_field(OpenApiTypes.DECIMAL)
class ChamaSerializer(serializers.ModelSerializer):
    total_contributions = serializers.SerializerMethodField()
    total_loans_outstanding = serializers.SerializerMethodField()

    class Meta:
        model = Chama
        fields = [
            "id", "name", "description", "created_at", "updated_at",
            "is_active", "total_contributions", "total_loans_outstanding",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def get_total_contributions(self, obj: Chama) -> Decimal:
        return obj.total_contributions()

    def get_total_loans_outstanding(self, obj: Chama) -> Decimal:
        return obj.total_loans_outstanding()


# ----------------------------------------------------------------------
# 2. MEMBER
# ----------------------------------------------------------------------
class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = [
            "id", "name", "phone", "email", "national_id",
            "created_at", "updated_at", "is_active",
        ]
        read_only_fields = ["created_at", "updated_at"]


# ----------------------------------------------------------------------
# 3. MEMBERSHIP
# ----------------------------------------------------------------------
class MembershipSerializer(serializers.ModelSerializer):
    member = MemberSerializer(read_only=True)
    chama = ChamaSerializer(read_only=True)
    member_id = serializers.PrimaryKeyRelatedField(
        queryset=Member.objects.all(), source="member", write_only=True
    )
    chama_id = serializers.PrimaryKeyRelatedField(
        queryset=Chama.objects.all(), source="chama", write_only=True
    )

    class Meta:
        model = Membership
        fields = [
            "id", "member", "chama", "member_id", "chama_id",
            "joined_at", "is_admin", "is_active",
        ]
        read_only_fields = ["joined_at"]

    def validate(self, attrs: dict) -> dict:
        member = attrs.get("member")
        chama = attrs.get("chama")
        if member and chama:
            if not member.is_active:
                raise serializers.ValidationError("Cannot join with inactive member.")
            if not chama.is_active:
                raise serializers.ValidationError("Cannot join inactive chama.")
        return attrs


# ----------------------------------------------------------------------
# 4. CONTRIBUTION
# ----------------------------------------------------------------------
class ContributionSerializer(serializers.ModelSerializer):
    membership = serializers.PrimaryKeyRelatedField(
        queryset=Membership.objects.select_related("member", "chama").all()
    )
    member_name = serializers.CharField(source="membership.member.name", read_only=True)
    chama_name = serializers.CharField(source="membership.chama.name", read_only=True)

    class Meta:
        model = Contribution
        fields = [
            "id", "membership", "member_name", "chama_name",
            "amount", "date", "transaction_ref", "confirmed",
        ]
        read_only_fields = ["date"]

    def validate(self, attrs: dict) -> dict:
        membership: Membership = attrs["membership"]
        amount: Decimal = attrs["amount"]

        if not membership.is_active:
            raise serializers.ValidationError("Cannot contribute to inactive membership.")
        if not membership.member.is_active:
            raise serializers.ValidationError("Cannot contribute for inactive member.")
        if amount <= Decimal("0"):
            raise serializers.ValidationError("Amount must be positive.")
        return attrs

    def create(self, validated_data: dict) -> Contribution:
        validated_data["confirmed"] = False
        return super().create(validated_data)


# ----------------------------------------------------------------------
# 5. LOAN APPLICATION & SERIALIZER
# ----------------------------------------------------------------------
class LoanApplicationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Loan
        fields = ["principal", "tenure_months", "interest_rate"]

    def validate_principal(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Principal must be positive.")
        return value

    def validate_tenure_months(self, value: int) -> int:
        if value <= 0:
            raise serializers.ValidationError("Tenure must be at least 1 month.")
        return value

    def validate(self, data: dict) -> dict:
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            raise serializers.ValidationError("Authentication required.")

        try:
            member = Member.objects.get(user=request.user)
        except Member.DoesNotExist:
            raise serializers.ValidationError("User has no member profile.")

        active_membership = member.memberships.filter(is_active=True).first()
        if not active_membership:
            raise serializers.ValidationError("You are not in any active chama.")

        total_saved = active_membership.contributions.filter(confirmed=True).aggregate(
            t=Sum("amount")
        )["t"] or Decimal("0.00")

        required = data["principal"] * Decimal("3")
        if total_saved < required:
            raise serializers.ValidationError(
                f"Insufficient savings. Need KES {required:,.2f}, you have KES {total_saved:,.2f}."
            )

        data["membership"] = active_membership
        return data


class LoanSerializer(serializers.ModelSerializer):
    membership = serializers.PrimaryKeyRelatedField(
        queryset=Membership.objects.select_related("member", "chama").all()
    )
    member_name = serializers.CharField(source="membership.member.name", read_only=True)
    chama_name = serializers.CharField(source="membership.chama.name", read_only=True)

    emi = serializers.SerializerMethodField()
    total_repayable = serializers.SerializerMethodField()
    total_paid = serializers.SerializerMethodField()
    balance_due = serializers.SerializerMethodField()

    class Meta:
        model = Loan
        fields = [
            "id", "membership", "member_name", "chama_name",
            "principal", "interest_rate", "tenure_months",
            "status", "applied_at", "approved_at",
            "emi", "total_repayable", "total_paid", "balance_due",
        ]
        read_only_fields = [
            "status", "applied_at", "approved_at",
            "emi", "total_repayable", "total_paid", "balance_due",
        ]

    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_emi(self, obj: Loan) -> Decimal:
        return obj.emi

    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_total_repayable(self, obj: Loan) -> Decimal:
        return obj.total_repayable

    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_total_paid(self, obj: Loan) -> Decimal:
        return obj.total_paid

    @extend_schema_field(OpenApiTypes.DECIMAL)
    def get_balance_due(self, obj: Loan) -> Decimal:
        return obj.balance_due


# ----------------------------------------------------------------------
# 6. REPAYMENT
# ----------------------------------------------------------------------
class RepaymentSerializer(serializers.ModelSerializer):
    loan = serializers.PrimaryKeyRelatedField(
        queryset=Loan.objects.select_related("membership__member").all()
    )
    member_name = serializers.CharField(source="loan.membership.member.name", read_only=True)
    chama_name = serializers.CharField(source="loan.membership.chama.name", read_only=True)

    class Meta:
        model = Repayment
        fields = [
            "id", "loan", "member_name", "chama_name",
            "amount", "date", "transaction_ref",
        ]
        read_only_fields = ["date"]

    def validate(self, attrs: dict) -> dict:
        loan: Loan = attrs["loan"]
        amount: Decimal = attrs["amount"]

        if amount <= 0:
            raise serializers.ValidationError("Repayment amount must be positive.")

        if amount > loan.balance_due:
            raise serializers.ValidationError(
                f"Cannot repay {amount}. Balance due is {loan.balance_due}."
            )

        if not loan.membership.is_active:
            raise serializers.ValidationError("Cannot repay on inactive membership.")

        return attrs


# ----------------------------------------------------------------------
# 7. M-PESA TRANSACTION
# ----------------------------------------------------------------------
class MpesaTransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = MpesaTransaction
        fields = [
            "id", "phone", "amount", "transaction_type",
            "checkout_request_id", "mpesa_receipt", "status",
            "raw_callback", "created_at",
        ]
        read_only_fields = [
            "checkout_request_id", "mpesa_receipt", "status", "created_at"
        ]

    def validate_phone(self, value: str) -> str:
        # Normalize: 07... → 2547..., +254... → 254...
        if value.startswith("0"):
            value = "254" + value[1:]
        elif value.startswith("+254"):
            value = "254" + value[4:]
        elif not value.startswith("254"):
            raise serializers.ValidationError("Phone must start with 2547...")

        if not (12 <= len(value) <= 12):
            raise serializers.ValidationError("Phone must be 12 digits (2547XXXXXXXX).")

        return value

    def validate_amount(self, value: Decimal) -> Decimal:
        if value <= 0:
            raise serializers.ValidationError("Amount must be positive.")
        return value
    
class MpesaCallbackSerializer(serializers.Serializer):
    Body = serializers.DictField()

    def validate_Body(self, value):
        if "stkCallback" not in value:
            raise serializers.ValidationError("Missing stkCallback")
        return value    