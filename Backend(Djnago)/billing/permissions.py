# billing/permissions.py
from rest_framework.permissions import BasePermission

class IsAdminUserOnly(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and request.user.is_staff
        )


class AdminGetMerchantGetAdminPostOnly(BasePermission):
    """
    GET  -> IsAdminUserOnly OR IsMerchantUserOnly
    POST -> IsAdminUserOnly
    """

    def has_permission(self, request, view):
        user = request.user

        if not user or not user.is_authenticated:
            print("User is not authenticated")
            return False

        # POST → ONLY ADMIN
        if request.method == "POST":
            return user.is_superadmin is True

        # GET → ADMIN OR MERCHANT
        if request.method == "GET":
            return (
                user.is_superadmin is True
                or user.is_staff is True
                or user.is_tenant is True
            )

        return False