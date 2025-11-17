class OrganizationContext:
    def __init__(self, organization):
        self.organization = organization
    
    def __enter__(self):
        from django.db import models
        models.tenant_context.set(self.organization)
        return self.organization
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        from django.db import models
        models.tenant_context.set(None)


def get_organization_aware_manager(manager_class):
    """Decorator to make model managers organization-aware"""
    class OrganizationAwareManager(manager_class):
        def get_queryset(self):
            from django.db import models
            qs = super().get_queryset()
            organization = models.tenant_context.get()
            if organization:
                return qs.filter(organization=organization)
            return qs

        def for_organization(self, organization):
            return self.get_queryset().filter(organization=organization)
    
    return OrganizationAwareManager
