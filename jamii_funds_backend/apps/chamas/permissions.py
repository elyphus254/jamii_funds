# chamas/permissions.py
from rest_framework import permissions

class IsAdminMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.membership.filter(user=request.user, role='admin').exists()

class IsCreatorOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.created_by == request.user or \
               obj.membership.filter(user=request.user, role='admin').exists()