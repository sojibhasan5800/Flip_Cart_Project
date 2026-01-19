from django.http import JsonResponse
from django_tenants.utils import get_tenant
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError


class TenantAdminMiddleware:

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        if not request.path.startswith("/api/admin_core/check"):
            return self.get_response(request)

        # 🔹 Resolve tenant
        try:
            tenant = get_tenant(request)
        except Exception:
            tenant = None
        
        print("HOST:", request.get_host())
        print("tenant:", tenant)


        # 🔹 JWT decode
        auth_header = request.META.get("HTTP_AUTHORIZATION")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JsonResponse(
                {"detail": "Authentication required", "is_public_admin": False},
                status=401
            )

        raw_token = auth_header.split(" ")[1]

        try:
            validated_token = JWTAuthentication().get_validated_token(raw_token)
            user = JWTAuthentication().get_user(validated_token)
        except (TokenError, InvalidToken):
            return JsonResponse(
                {"detail": "Invalid or expired token", "is_public_admin": False},
                status=401
            )

        # 🔹 Only public schema admin allowed

        if not tenant or tenant.schema_name != "dev_user":
            return JsonResponse(
                {"detail": "Not public schema", "is_public_admin": False},
                status=403
            )
       
        # 🔹 Role checks
        if not user.is_authenticated:
            return JsonResponse(
                {"detail": "Authentication required", "is_public_admin": False},
                status=401
            )

        if not user.is_staff:
            return JsonResponse(
                {"detail": "Admin access denied", "is_public_admin": False},
                status=403
            )

        if not user.is_superadmin:
            return JsonResponse(
                {"detail": "Only superadmin allowed", "is_public_admin": False},
                status=403
            )

        # ✅ Allowed
        request.user = user
        request.is_public_admin = True

        return self.get_response(request)
