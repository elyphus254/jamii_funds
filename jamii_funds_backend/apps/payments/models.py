from django.db import models

from apps.chamas.models import Member

    
class Payment(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20)
    amount = models.DecimalField(max_digits=12, decimal_places=2)

    checkout_request_id = models.CharField(max_length=200, null=True, blank=True)
    merchant_request_id = models.CharField(max_length=200, null=True, blank=True)

    status = models.CharField(max_length=20, default="Pending")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member} - {self.amount} ({self.status})"