# permissions.py
from rest_framework import permissions
from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superadmin)
        )


class IsTenantAdmin(permissions.BasePermission):
    """
    Check if user is admin of the current tenant
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superuser can access all
        if request.user.is_superadmin:
            return True
        
        # Check if user has tenant and is admin/staff
        if hasattr(request.user, 'tenant'):
            # Add your tenant admin logic here
            # For example, check user role in tenant
            return request.user.is_staff or request.user.is_admin
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # User can only access coupons from their own tenant
        if hasattr(request.user, 'tenant'):
            return obj.tenant == request.user.tenant
        return False