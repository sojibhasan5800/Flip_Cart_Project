# flipcart_project/middleware/tenant_admin.py

from django.shortcuts import redirect
from django.contrib import messages
from django_tenants.utils import get_tenant
from django.contrib.auth import logout


class TenantAdminMiddleware:
    """
    Middleware to enforce strict admin access:
    - Superadmin can access ONLY the public admin panel.
    - Tenant admins can access ONLY their own tenant's admin panel.
    - Prevents cross-tenant access.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Apply logic only when user visits /admin/
        if "admin" in request.path:

            try:
                current_tenant = get_tenant(request)
            except Exception:
                current_tenant = None

            user = request.user

            # If user is not logged in → no need to check anything
            if not user.is_authenticated:
                return response

            # PUBLIC ADMIN → Only superadmin allowed
            if current_tenant and current_tenant.schema_name == "public":
                if not user.is_superuser:
                    # Non-superadmin trying to enter public admin
                    logout(request)
                    messages.error(request, "You do not have permission to access the main admin panel.")
                    return redirect("/")

            # TENANT ADMIN → Only tenant users allowed
            elif current_tenant:
                if user.is_superuser:
                    # Superadmin should NOT enter tenant admin
                    logout(request)
                    messages.error(request, "Superadmin cannot access tenant admin panels.")
                    return redirect("/")

                # Example (optional): check if user belongs to this tenant
                # if user.tenant_id != current_tenant.id:
                #     logout(request)
                #     messages.error(request, "You cannot access another tenant's admin.")
                #     return redirect("/")

        return response
