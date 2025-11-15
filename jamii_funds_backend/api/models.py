# api/models.py
from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone

# ----------------------------------------------------------------------
# 1. Chama (Savings Group)
# ----------------------------------------------------------------------
class Chama(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Chama"
        verbose_name_plural = "Chamas"
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["name"])]

    def __str__(self) -> str:
        return self.name

    # ----- Aggregations -------------------------------------------------
    def total_contributions(self) -> Decimal:
        """Sum of all confirmed contributions in this chama."""
        total = self.contributions.aggregate(s=models.Sum("amount"))["s"]
        return total or Decimal("0.00")

    def total_loans_outstanding(self) -> Decimal:
        """Principal of all loans that are not fully repaid."""
        total = self.loans.filter(status__in=["Pending", "Approved"]).aggregate(
            s=models.Sum("principal")
        )["s"]
        return total or Decimal("0.00")


# ----------------------------------------------------------------------
# 2. Member
# ----------------------------------------------------------------------
class Member(models.Model):
    name = models.CharField(max_length=255)
    phone = models.CharField(max_length=20, unique=True)
    email = models.EmailField(blank=True, null=True)
    national_id = models.CharField(max_length=30, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["phone"]),
            models.Index(fields=["national_id"]),
        ]

    def __str__(self) -> str:
        return self.name

    # ----- Convenience --------------------------------------------------
    def total_contributed(self) -> Decimal:
        total = self.contributions.aggregate(s=models.Sum("amount"))["s"]
        return total or Decimal("0.00")

    def active_loans_balance(self) -> Decimal:
        total = self.loans.filter(status__in=["Pending", "Approved"]).aggregate(
            s=models.Sum("principal")
        )["s"]
        return total or Decimal("0.00")


# ----------------------------------------------------------------------
# 3. Membership (Member ↔ Chama bridge)
# ----------------------------------------------------------------------
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

    def __str__(self) -> str:
        return f"{self.member.name} → {self.chama.name}"


# ----------------------------------------------------------------------
# 4. Contribution
# ----------------------------------------------------------------------
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
    confirmed = models.BooleanField(default=False)   # M-Pesa callback, manual, etc.

    class Meta:
        ordering = ["-date"]
        indexes = [
            models.Index(fields=["date"]),
            models.Index(fields=["membership"]),
        ]

    def __str__(self) -> str:
        return f"{self.membership.member.name} → {self.amount} ({self.date.date()})"

    @property
    def chama(self) -> Chama:
        return self.membership.chama

    @property
    def member(self) -> Member:
        return self.membership.member


# ----------------------------------------------------------------------
# 5. Loan
# ----------------------------------------------------------------------
class Loan(models.Model):
    STATUS_CHOICES = [
        ("Pending", "Pending"),
        ("Approved", "Approved"),
        ("Rejected", "Rejected"),
        ("Repaid", "Repaid"),
        ("Defaulted", "Defaulted"),
    ]

    membership = models.ForeignKey(
        Membership, on_delete=models.CASCADE, related_name="loans"
    )
    principal = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=Decimal("1.50"),
        help_text="Monthly interest rate in percent (e.g. 1.5 for 1.5%).",
    )
    tenure_months = models.PositiveSmallIntegerField(default=12)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="Pending")
    applied_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    disbursed_at = models.DateTimeField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)   # optional final deadline

    class Meta:
        ordering = ["-applied_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["membership"]),
        ]

    def __str__(self) -> str:
        return f"Loan {self.principal} → {self.membership.member.name}"

    # ----- EMI & Repayment helpers ------------------------------------
    @property
    def monthly_rate(self) -> Decimal:
        return self.interest_rate / Decimal("100")

    @property
    def emi(self) -> Decimal:
        """Equated Monthly Installment."""
        p = self.principal
        r = self.monthly_rate
        n = self.tenure_months
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

    @property
    def chama(self) -> Chama:
        return self.membership.chama

    @property
    def member(self) -> Member:
        return self.membership.member


# ----------------------------------------------------------------------
# 6. Repayment (optional – tracks each payment)
# ----------------------------------------------------------------------
class Repayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="repayments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(default=timezone.now)
    transaction_ref = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["-date"]

    def __str__(self) -> str:
        return f"Repayment {self.amount} on {self.loan}"


# ----------------------------------------------------------------------
# 7. InterestEntry (monthly accrual)
# ----------------------------------------------------------------------
class InterestEntry(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="interest_entries")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    month = models.DateField()   # first day of the month
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("loan", "month")
        ordering = ["-month"]

    def __str__(self) -> str:
        return f"Interest {self.amount} for {self.loan} ({self.month})"


# ----------------------------------------------------------------------
# 8. ProfitDistribution + per-member share
# ----------------------------------------------------------------------
class ProfitDistribution(models.Model):
    chama = models.ForeignKey(
        Chama, on_delete=models.CASCADE, related_name="profit_distributions"
    )
    year = models.PositiveSmallIntegerField()
    total_profit = models.DecimalField(max_digits=14, decimal_places=2)
    distributed_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ("chama", "year")
        ordering = ["-year"]

    def __str__(self) -> str:
        return f"{self.chama.name} Profit {self.year}"


class MemberProfitShare(models.Model):
    distribution = models.ForeignKey(
        ProfitDistribution, on_delete=models.CASCADE, related_name="shares"
    )
    membership = models.ForeignKey(Membership, on_delete=models.CASCADE)
    share_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid = models.BooleanField(default=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("distribution", "membership")

    def __str__(self) -> str:
        return f"{self.membership.member.name} → {self.share_amount}"