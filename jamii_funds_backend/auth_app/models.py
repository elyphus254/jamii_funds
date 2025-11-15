# auth_app/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model with phone number as optional unique identifier.
    Username is still required for login (you can change to phone/email later).
    """
    phone_regex = RegexValidator(
        regex=r'^\+?1?\d{9,15}$',
        message="Phone number must be entered in the format: '+254712345678'. Up to 15 digits allowed."
    )

    phone_number = models.CharField(
        max_length=17,
        unique=True,
        blank=True,
        null=True,
        validators=[phone_regex],
        help_text="User's mobile number (e.g. +254712345678)"
    )
    is_verified = models.BooleanField(
        default=False,
        help_text="Set to True when user verifies phone/email"
    )
    date_verified = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Fix reverse accessor clashes
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"
        ordering = ['-date_joined']
        indexes = [
            models.Index(fields=['phone_number']),
            models.Index(fields=['is_verified']),
        ]

    def __str__(self):
        return self.username or self.phone_number or f"User {self.id}"

    def verify(self):
        """Mark user as verified (e.g., after SMS OTP)"""
        self.is_verified = True
        self.date_verified = timezone.now()
        self.save(update_fields=['is_verified', 'date_verified'])

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username