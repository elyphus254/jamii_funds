from django.db import models
from django.conf import settings
from apps.chamas.models import Chama, Member


class ContributionType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True)
    default_amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_fixed = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Contribution(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    type = models.ForeignKey(ContributionType, on_delete=models.SET_NULL, null=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateTimeField(auto_now_add=True)
    reference = models.CharField(max_length=100, blank=True, null=True)


    def __str__(self):
        return f"{self.member} - {self.amount}"
