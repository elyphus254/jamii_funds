# core/models.py
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.conf import settings

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser


# ------------------------------------------------------------------
# 1. CHAMA
# ------------------------------------------------------------------
class Chama(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    def total_contributions(self) -> Decimal:
        total = self.contributions.aggregate(s=models.Sum("amount"))["s"]
        return total or Decimal("0.00")

    def total_loans_outstanding(self) -> Decimal:
        total = self.loans.filter(
            status__in=[Loan.STATUS_PENDING, Loan.STATUS_APPROVED]
        ).aggregate(s=models.Sum("principal"))["s"]
        return total or Decimal("0.00")


# ------------------------------------------------------------------
# 2. MEMBER
# ------------------------------------------------------------------
class Member(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    national_id = models.CharField(max_length=30, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="member_profile",
        null=True,
        blank=True,
    )

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["national_id"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return self.name

    @property
    def active_memberships(self):
        return self.memberships.filter(is_active=True)


# ------------------------------------------------------------------
# 3. MEMBERSHIP
# ------------------------------------------------------------------
class Membership(models.Model):
    member = models.ForeignKey(
        Member, on_delete=models.CASCADE, related_name="memberships"
    )
    chama = models.ForeignKey(
        Chama, on_delete=models.CASCADE, related_name="memberships"
    )
    joined_at = models.DateTimeField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ("member", "chama")
        ordering = ["-joined_at"]
        indexes = [
            models.Index(fields=["member", "chama"]),
            models.Index(fields=["is_admin"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self) -> str:
        return f"{self.member.name} → {self.chama.name}"


# ------------------------------------------------------------------
# 4. CONTRIBUTION
# ------------------------------------------------------------------
class Contribution(models.Model):
    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name="contributions"
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.01"))],
    )
    date = models.DateTimeField(default=timezone.now)
    transaction_ref = models.CharField(max_length=120, blank=True)
    confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["membership"]),
            models.Index(fields=["date"]),
            models.Index(fields=["confirmed"]),
        ]

    def __str__(self) -> str:
        return f"{self.membership.member.name} → KES {self.amount}"

    def save(self, *args, **kwargs):
        # Auto-link chama via membership
        if not hasattr(self, "chama") and self.membership:
            self.chama = self.membership.chama
        super().save(*args, **kwargs)


# ------------------------------------------------------------------
# 5. LOAN
# ------------------------------------------------------------------
class Loan(models.Model):
    STATUS_PENDING = "Pending"
    STATUS_APPROVED = "Approved"
    STATUS_REJECTED = "Rejected"
    STATUS_REPAID = "Repaid"

    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending"),
        (STATUS_APPROVED, "Approved"),
        (STATUS_REJECTED, "Rejected"),
        (STATUS_REPAID, "Repaid"),
    ]

    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name="loans"
    )
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=Decimal("1.50")
    )  # % per month
    tenure_months = models.PositiveSmallIntegerField(default=12)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING
    )
    applied_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-applied_at"]
        indexes = [
            models.Index(fields=["membership"]),
            models.Index(fields=["status"]),
            models.Index(fields=["applied_at"]),
        ]

    def __str__(self) -> str:
        return f"Loan KES {self.principal} → {self.membership.member.name}"

    @property
    def monthly_rate(self) -> Decimal:
        return self.interest_rate / Decimal("100")

    @property
    def emi(self) -> Decimal:
        p, r, n = self.principal, self.monthly_rate, self.tenure_months
        if r == 0:
            return p / n
        return p * r * (1 + r) ** n / ((1 + r) ** n - 1)

    @property
    def total_repayable(self) -> Decimal:
        return self.emi * self.tenure_months

    @property
    def total_paid(self) -> Decimal:
        total = self.repayments.aggregate(s=models.Sum("amount"))["s"]
        return total or Decimal("0.00")

    @property
    def balance_due(self) -> Decimal:
        return self.total_repayable - self.total_paid

    def approve(self, approved_by: "AbstractUser | None" = None) -> None:
        if self.status != self.STATUS_PENDING:
            raise ValueError("Only pending loans can be approved.")
        with transaction.atomic():
            self.status = self.STATUS_APPROVED
            self.approved_at = timezone.now()
            self.save()
            # Optional: create first interest entry
            # InterestEntry.record_for_loan(self)


# ------------------------------------------------------------------
# 6. REPAYMENT
# ------------------------------------------------------------------
class Repayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="repayments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    transaction_ref = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-date"]
        indexes = [models.Index(fields=["loan"]), models.Index(fields=["date"])]

    def __str__(self) -> str:
        return f"Repayment KES {self.amount} on {self.loan}"


# ------------------------------------------------------------------
# 7. M-PESA TRANSACTION
# ------------------------------------------------------------------
class MpesaTransaction(models.Model):
    TYPE_CONTRIBUTION = "Contribution"
    TYPE_LOAN_REPAYMENT = "Loan Repayment"

    TRANSACTION_TYPES = [
        (TYPE_CONTRIBUTION, "Contribution"),
        (TYPE_LOAN_REPAYMENT, "Loan Repayment"),
    ]

    phone = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(
        max_length=40, choices=TRANSACTION_TYPES, default=TYPE_CONTRIBUTION
    )
    checkout_request_id = models.CharField(max_length=120, blank=True, null=True)
    mpesa_receipt = models.CharField(max_length=120, unique=True, blank=True, null=True)
    status = models.CharField(max_length=40, default="Pending")
    raw_callback = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["mpesa_receipt"]),
            models.Index(fields=["status"]),
            models.Index(fields=["checkout_request_id"]),
        ]

    def __str__(self) -> str:
        return f"{self.phone} - KES {self.amount} ({self.transaction_type})"