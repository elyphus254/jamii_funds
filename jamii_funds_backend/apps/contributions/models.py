from django.db import models
from django.conf import settings
from apps.chamas.models import Chama

class Contribution(models.Model):
    member = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='contributions'
    )
    chama = models.ForeignKey(
        Chama,
        on_delete=models.CASCADE,
        related_name='contributions'
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_transaction = models.OneToOneField(
        'payments.MpesaTransaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contribution'
    )
    contributed_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    class Meta:
        ordering = ['-contributed_at']
        unique_together = ['member', 'chama', 'contributed_at']

    def __str__(self):
        return f"{self.member} → {self.chama}: KES {self.amount}"