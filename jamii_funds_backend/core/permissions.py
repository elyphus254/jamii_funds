# core/permissions.py
from __future__ import annotations

from typing import TYPE_CHECKING

from rest_framework import permissions
from drf_spectacular.utils import extend_schema

if TYPE_CHECKING:
    from django.contrib.auth.models import AbstractUser
    from rest_framework.request import Request
    from .models import Chama, Member


@extend_schema(description="User is admin of the Chama")
class IsChamaAdmin(permissions.BasePermission):
    """
    Allows access only to admins of the specific Chama.
    Works on:
      - Chama object (detail view)
      - Loan/Contribution (via chama relation)
    """

    def has_permission(self, request: "Request", view) -> bool:
        # Allow list/create if user is admin in *any* chama
        return request.user.memberships.filter(is_admin=True).exists()

    def has_object_permission(self, request: "Request", view, obj) -> bool:
        # obj could be Chama, Loan, Contribution, etc.
        chama = self._get_chama(obj)
        if not chama:
            return False
        return chama.members.filter(user=request.user, is_admin=True).exists()

    def _get_chama(self, obj) -> "Chama | None":
        """Extract Chama from obj (supports Chama, Loan, Contribution, etc.)"""
        if hasattr(obj, "chama"):
            return obj.chama
        if hasattr(obj, "member") and hasattr(obj.member, "chama"):
            return obj.member.chama
        return None


@extend_schema(description="User is a member of the Chama")
class IsMemberOfChama(permissions.BasePermission):
    """
    Allows access if user is a member of the Chama.
    Works on:
      - List: any chama membership
      - Object: chama-specific (Loan, Contribution, etc.)
    """

    def has_permission(self, request: "Request", view) -> bool:
        # Allow list/create if user is in *any* chama
        return request.user.memberships.exists()

    def has_object_permission(self, request: "Request", view, obj) -> bool:
        # Extract chama from object
        chama = self._get_chama(obj)
        if not chama:
            return False
        return chama.members.filter(user=request.user).exists()

    def _get_chama(self, obj) -> "Chama | None":
        """Support Chama, Loan, Contribution, Repayment, etc."""
        if hasattr(obj, "chama"):
            return obj.chama
        if hasattr(obj, "member") and hasattr(obj.member, "chama"):
            return obj.member.chama
        if hasattr(obj, "loan") and hasattr(obj.loan, "member"):
            return obj.loan.member.chama
        return None