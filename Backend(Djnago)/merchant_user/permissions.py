# permissions.py
from operator import is_
from rest_framework.permissions import BasePermission

class IsSuperAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user
            and request.user.is_authenticated
            and (request.user.is_staff or request.user.is_superuser)
        )

class IsMerchantUser(BasePermission):
    message = "You are not a verified merchant for this organization"

    def has_permission(self, request, view):
        user = request.user

        org_id = request.data.get("organization_id") or request.query_params.get("organization_id")
        if not user or not user.is_authenticated or not org_id:
            return False

        try:
            org_id = int(org_id)
        except ValueError:
            return False

        # check if user is verified merchant in this org
        is_merchant = user.merchant_profile.filter(
            organization_id=org_id,
            is_verified=True,
            is_active=True
        ).exists()

        return is_merchant
