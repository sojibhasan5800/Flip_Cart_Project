class TenantContext:
    def __init__(self, tenant):
        self.tenant = tenant
    
    def __enter__(self):
        from django.db import models
        models.tenant_context.set(self.tenant)
        return self.tenant
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        from django.db import models
        models.tenant_context.set(None)

def get_tenant_aware_manager(manager_class):
    """Decorator to make managers tenant-aware"""
    class TenantAwareManager(manager_class):
        def get_queryset(self):
            from django.db import models
            qs = super().get_queryset()
            tenant = models.tenant_context.get()
            if tenant:
                return qs.filter(tenant=tenant)
            return qs
        
        def for_tenant(self, tenant):
            return self.get_queryset().filter(tenant=tenant)
    
    return TenantAwareManager