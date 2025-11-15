from rest_framework import permissions

class IsChamaAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        # obj is Chama
        return obj.members.filter(user=request.user, is_admin=True).exists()

class IsMemberOfChama(permissions.BasePermission):
    def has_permission(self, request, view):
        # For list/create: check if user is in any chama
        return request.user.memberships.exists()

    def has_object_permission(self, request, view, obj):
        # obj could be Loan, Member, etc.
        return obj.member.chama.members.filter(user=request.user).exists()