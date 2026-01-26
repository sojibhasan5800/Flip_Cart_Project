import json
from django_tenants.utils import schema_context
from merchant_user.models import Organization
from django.core.exceptions import ObjectDoesNotExist


class MerchantProductMiddleware:
    """
    This middleware switches schema ONLY for merchant product related endpoints:
    - /api/merchant_user/merchant-products/
    - /api/merchant_user/products/<pk>/toggle-stock/
    """

    # একাধিক path support করার জন্য list ব্যবহার করা হলো
    TARGET_PATHS = [
        "/api/merchant_user/merchant-products/",
        "/api/merchant_user/products/toggle-stock/",   # toggle-stock এর prefix
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):

        # 🔹 Check if request path starts with any of the target prefixes
        if not any(request.path.startswith(path) for path in self.TARGET_PATHS):
            return self.get_response(request)

        org_id = request.headers.get("X-ORG-ID") or request.GET.get("organization_id")

        if not org_id and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = json.loads(request.body)
                org_id = body.get("organization_id")
            except (json.JSONDecodeError, TypeError):
                org_id = None
        if not org_id:
            return self.get_response(request)

        try:
            organization = Organization.objects.get(
                id=org_id,
                is_active=True,
                is_verified=True
            )
        except ObjectDoesNotExist:
            return self.get_response(request)

        # 🔹 Attach organization to request
        request.organization = organization

        # 🔹 Switch schema safely
        with schema_context(organization.schema_name):
            response = self.get_response(request)

        return response
