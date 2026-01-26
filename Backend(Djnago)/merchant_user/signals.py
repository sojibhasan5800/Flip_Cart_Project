import re
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Organization, OrganizationDomain

@receiver(post_save, sender=Organization)
def create_primary_domain(sender, instance, created, **kwargs):
    if not created:
        return

    base_domain = getattr(settings, "BASE_ORGANIZATION_DOMAIN", None)
    if not base_domain:
        return

    # subdomain = username (or schema_name)
    raw_subdomain = instance.username or instance.business_name
    subdomain = raw_subdomain.lower()
    subdomain = subdomain.replace(" ", "-").replace(".", "")
    subdomain = re.sub(r"[^a-z0-9-]", "", subdomain)
    
    full_domain = f"{subdomain}.{base_domain}"

    counter = 1
    while OrganizationDomain.objects.filter(domain=full_domain).exists():
        full_domain = f"{subdomain}{counter}.{base_domain}"
        counter += 1

    OrganizationDomain.objects.create(
        tenant=instance,
        domain=full_domain,
        is_primary=True,
        domain_type="primary"
    )
