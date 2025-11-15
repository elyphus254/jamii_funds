from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from decimal import Decimal
from django.utils import timezone


# ==============================
# 1. CHAMA (Savings Group)
# ==============================
class Chama(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    till_number = models.CharField(max_length=20, blank=True, null=True, unique=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='created_chamas'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Chama"
        verbose_name_plural = "Chamas"
        ordering = ['-created_at']

    def __str__(self):
        return self.name

    def total_contributions(self):
        return self.contributions.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    def total_loans_outstanding(self):
        return self.loans.filter(status='Approved').aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')


# ==============================
# 2. MEMBER (User in a Chama)
# ==============================
class Member(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='memberships'
    )
    chama = models.ForeignKey(
        Chama,
        on_delete=models.CASCADE,
        related_name='members'
    )
    joined_date = models.DateField(auto_now_add=True)
    is_admin = models.BooleanField(default=False)  # Chama admin
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'chama')  # One user per chama
        ordering = ['-joined_date']

    def __str__(self):
        return f"{self.user.get_full_name()} ({self.chama.name})"

    def total_contributed(self):
        return self.contributions.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    def outstanding_loans(self):
        return self.loans.filter(status__in=['Pending', 'Approved']).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0.00')


# ==============================
# 3. CONTRIBUTION
# ==============================
class Contribution(models.Model):
    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='contributions'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('1.00'))]
    )
    date = models.DateTimeField(auto_now_add=True)
    transaction_ref = models.CharField(max_length=100, blank=True)  # M-Pesa, bank, etc.
    confirmed = models.BooleanField(default=False)  # Manual or callback confirm

    class Meta:
        ordering = ['-date']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['member']),
        ]

    def __str__(self):
        return f"{self.member.user.get_full_name()} → {self.amount} ({self.date.date()})"

    def save(self, *args, **kwargs):
        # Auto-link chama via member
        if not hasattr(self, 'chama') and self.member:
            self.chama = self.member.chama
        super().save(*args, **kwargs)


# ==============================
# 4. LOAN
# ==============================
class Loan(models.Model):
    STATUS_CHOICES = [
        ('Pending', 'Pending'),
        ('Approved', 'Approved'),
        ('Rejected', 'Rejected'),
        ('Repaid', 'Repaid'),
        ('Defaulted', 'Defaulted'),
    ]

    member = models.ForeignKey(
        Member,
        on_delete=models.CASCADE,
        related_name='loans'
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('1.50'))  # Monthly
    tenure_months = models.PositiveIntegerField(default=12)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Pending')
    applied_date = models.DateTimeField(auto_now_add=True)
    approved_date = models.DateTimeField(null=True, blank=True)
    disbursed_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-applied_date']

    def __str__(self):
        return f"{self.member} - {self.amount} ({self.status})"

    @property
    def monthly_repayment(self):
        if self.tenure_months == 0:
            return self.amount
        principal = self.amount
        monthly_rate = self.interest_rate / 100
        # EMI Formula
        return principal * monthly_rate * (1 + monthly_rate)**self.tenure_months / \
               ((1 + monthly_rate)**self.tenure_months - 1)

    @property
    def total_repayable(self):
        return self.monthly_repayment * self.tenure_months

    def total_paid(self):
        return self.repayments.aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')

    def balance_due(self):
        return self.total_repayable - self.total_paid()


# ==============================
# 5. LOAN REPAYMENT
# ==============================
class Repayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    transaction_ref = models.CharField(max_length=100, blank=True)

    class Meta:
        ordering = ['-date']

    def __str__(self):
        return f"Repayment {self.amount} on {self.loan}"


# ==============================
# 6. INTEREST ENTRY (Monthly Accrual)
# ==============================
class InterestEntry(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='interest_entries')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()  # First day of the month
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('loan', 'month')
        ordering = ['-month']

    def __str__(self):
        return f"Interest {self.amount} for {self.loan.member} ({self.month})"


# ==============================
# 7. PROFIT DISTRIBUTION
# ==============================
class ProfitDistribution(models.Model):
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='profit_distributions')
    year = models.PositiveIntegerField()
    total_profit = models.DecimalField(max_digits=14, decimal_places=2)
    distributed_date = models.DateField()
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ('chama', 'year')
        ordering = ['-year']

    def __str__(self):
        return f"{self.chama.name} Profit {self.year}: {self.total_profit}"


class MemberProfitShare(models.Model):
    distribution = models.ForeignKey(ProfitDistribution, on_delete=models.CASCADE, related_name='shares')
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    share_amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('distribution', 'member')

    def __str__(self):
        return f"{self.member} → {self.share_amount}"