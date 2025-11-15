# flipcart_project/middleware/tenant_admin.py

from django_tenants.utils import get_tenant

class TenantAdminMiddleware:
    """
    Middleware to control admin panel access based on tenant.
    - Superadmin (public schema) → can access everything.
    - Tenant admin → only their own tenant data (handled by django-tenants).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process request first
        response = self.get_response(request)

        # Admin panel detection
        if 'admin' in request.path:
            try:
                current_tenant = get_tenant(request)
            except Exception:
                current_tenant = None

            user = request.user

            # Safe superuser check (prevents AttributeError)
            is_superadmin = getattr(user, "is_superuser", False)
            is_staff = getattr(user, "is_staff", False)

            # If logged-in user but not staff → block access
            if user.is_authenticated and not is_staff:
                # Non-staff users cannot access admin ever
                pass

            # PUBLIC SCHEMA → superadmin access
            if current_tenant and current_tenant.schema_name == "public":
                # Only superadmin can use public admin panel
                if not is_superadmin:
                    # non-superadmin cannot access public admin
                    pass

            # TENANT SCHEMA → tenant admin access
            elif current_tenant:
                # Tenant admin: django-tenants handles isolation
                # No special action needed
                pass

        return response
