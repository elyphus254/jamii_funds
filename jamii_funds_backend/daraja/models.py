# daraja/models.py
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
import uuid


class MpesaTransaction(models.Model):
    """
    Stores M-Pesa STK Push / C2B callback data.
    One record per transaction attempt.
    """
    TRANSACTION_TYPES = [
        ('CONTRIBUTION', 'Member Contribution'),
        ('LOAN_REPAYMENT', 'Loan Repayment'),
        ('FEE', 'Service Fee'),
        ('WITHDRAWAL', 'Chama Withdrawal'),
    ]

    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('INITIATED', 'STK Push Sent'),
        ('COMPLETED', 'Success'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('TIMEOUT', 'Timeout'),
    ]

    # Core fields
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='mpesa_transactions'
    )
    chama = models.ForeignKey(
        'core.Chama',
        on_delete=models.CASCADE,
        related_name='mpesa_transactions',
        null=True,
        blank=True
    )

    # Transaction details
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(1.00)]
    )
    phone_number = models.CharField(max_length=17)  # e.g. 2547xxxxxxxx
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES, default='CONTRIBUTION')

    # M-Pesa callback fields
    mpesa_receipt_number = models.CharField(max_length=50, unique=True, null=True, blank=True)
    merchant_request_id = models.CharField(max_length=100, null=True, blank=True)
    checkout_request_id = models.CharField(max_length=100, unique=True, null=True, blank=True)
    result_code = models.CharField(max_length=10, null=True, blank=True)
    result_desc = models.TextField(null=True, blank=True)

    # Status & timing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    initiated_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    callback_received_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    metadata = models.JSONField(default=dict, blank=True)  # Store raw callback

    class Meta:
        verbose_name = "M-Pesa Transaction"
        verbose_name_plural = "M-Pesa Transactions"
        ordering = ['-initiated_at']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['mpesa_receipt_number']),
            models.Index(fields=['checkout_request_id']),
            models.Index(fields=['status']),
            models.Index(fields=['transaction_type']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['merchant_request_id'],
                name='unique_merchant_request_id',
                condition=models.Q(merchant_request_id__isnull=False)
            ),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.amount} KES ({self.get_status_display()})"

    def mark_as_completed(self, receipt_number, callback_data=None):
        """Called when M-Pesa confirms payment."""
        self.status = 'COMPLETED'
        self.mpesa_receipt_number = receipt_number
        self.completed_at = timezone.now()
        self.callback_received_at = timezone.now()
        if callback_data:
            self.metadata = callback_data
        self.save()

    def mark_as_failed(self, result_code, result_desc):
        """Called on failure."""
        self.status = 'FAILED'
        self.result_code = result_code
        self.result_desc = result_desc
        self.callback_received_at = timezone.now()
        self.save()

    @property
    def is_successful(self):
        return self.status == 'COMPLETED'

    @property
    def short_phone(self):
        """Return last 10 digits for display"""
        return self.phone_number[-10:]

    def link_to_contribution(self):
        """Auto-link to Contribution if type is CONTRIBUTION"""
        if self.transaction_type == 'CONTRIBUTION' and self.is_successful:
            from core.models import Contribution, Membership
            membership = Membership.objects.filter(
                member__user=self.user,
                chama=self.chama
            ).first()
            if membership:
                Contribution.objects.create(
                    membership=membership,
                    amount=self.amount,
                    date=timezone.now(),
                    transaction_ref=self.mpesa_receipt_number,
                    confirmed=True
                )