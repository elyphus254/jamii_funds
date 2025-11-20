# models.py
from django.db import models
from django.conf import settings

class Chama(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='chamas_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through='Member',
        related_name='chamas_joined'
    )

    def __str__(self):
        return self.name

class Member(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    chama = models.ForeignKey(Chama, on_delete=models.CASCADE, related_name='membership')
    role = models.CharField(
        max_length=50,
        choices=(('admin', 'Admin'), ('member', 'Member')),
        default='member'
    )
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'chama')
      

    def __str__(self):
        return f"{self.user.username} in {self.chama.name} ({self.role})"