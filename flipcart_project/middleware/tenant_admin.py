# flipcart_project/middleware/tenant_admin.py

class TenantAdminMiddleware:
    """
    Middleware to control admin panel access based on the active tenant.
    - Super Admin (public schema) → Can access everything
    - Tenant Admin → Can access only their own tenant’s data
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request first
        response = self.get_response(request)

        # Detect if the request is for Django admin
        if 'admin' in request.path:
            try:
                from django_tenants.utils import get_tenant
                current_tenant = get_tenant(request)
            except Exception:
                current_tenant = None

            user = request.user

            # Safe superuser/staff check (prevents attribute errors)
            is_superadmin = getattr(user, "is_superuser", False)
            is_staff = getattr(user, "is_staff", False)

            # Logged-in user but not staff → block access
            if user.is_authenticated and not is_staff:
                from django.contrib import messages
                from django.shortcuts import redirect
                messages.error(request, "You don't have permission to access the admin panel.")
                return redirect('/')

            # Public schema admin access → only superadmins allowed
            if current_tenant and current_tenant.schema_name == "public":
                # Only superadmin can access public admin panel
                if not is_superadmin:
                    messages.error(request, "Only superadmin can access the public admin panel.")
                    return redirect('/')

            # Tenant schema admin access → tenant admin allowed
            elif current_tenant:
                # Tenant admin access is automatically handled by django-tenants
                # No special action needed here
                pass

        return response
