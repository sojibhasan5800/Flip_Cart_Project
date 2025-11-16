from django.http import Http404
from django.shortcuts import redirect
from accounts.models import Tenant
import re

class TenantMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        host = request.get_host()
        
        # Extract subdomain from host
        subdomain = self.extract_subdomain(host)
        
        if subdomain and subdomain not in ['www', 'admin', 'api']:
            try:
                tenant = Tenant.objects.get_by_subdomain(subdomain)
                request.tenant = tenant
                
                # Set tenant context for all requests
                if hasattr(request, 'user') and request.user.is_authenticated:
                    # Ensure user belongs to this tenant
                    if request.user.tenant != tenant and not request.user.is_platform_admin:
                        request.tenant = None
                        return redirect(f"https://{request.get_host().replace(subdomain + '.', '')}")
                        
            except Tenant.DoesNotExist:
                # Tenant not found - redirect to main site
                main_domain = self.get_main_domain(host)
                return redirect(f"https://{main_domain}")
        else:
            request.tenant = None

        response = self.get_response(request)
        return response

    def extract_subdomain(self, host):
        """Extract subdomain from hostname"""
        pattern = r'^(?:http://|https://)?([^\.]+)\.'
        match = re.match(pattern, host)
        if match:
            return match.group(1)
        return None

    def get_main_domain(self, host):
        """Get main domain from host"""
        parts = host.split('.')
        if len(parts) > 2:
            return '.'.join(parts[1:])
        return host