# merchant_user/context.py
from django.db import models
from threading import local

# Thread-local storage for organization context
_organization_context = local()

class OrganizationContext:
    def __init__(self, organization):
        self.organization = organization
    
    def __enter__(self):
        _organization_context.value = self.organization
        return self.organization
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        _organization_context.value = None

def get_organization_aware_manager(manager_class):
    """Decorator to make model managers organization-aware"""
    class OrganizationAwareManager(manager_class):
        def get_queryset(self):
            qs = super().get_queryset()
            # Check if organization context exists
            if hasattr(_organization_context, 'value') and _organization_context.value:
                return qs.filter(organization=_organization_context.value)
            return qs

        def for_organization(self, organization):
            return self.get_queryset().filter(organization=organization)
    
    return OrganizationAwareManager

# Helper function to get current organization
def get_current_organization():
    """Get current organization from context"""
    return getattr(_organization_context, 'value', None)