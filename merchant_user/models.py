from django.db import models
import uuid
# Create your models here.



class OrganizationManager(models.Manager):
    def get_by_subdomain(self, subdomain):
        return self.get(subdomain=subdomain, is_active=True)

class Organization(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    subdomain = models.CharField(max_length=50, unique=True)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    objects = OrganizationManager()
    
    def __str__(self):
        return f"{self.name} ({self.subdomain})"
    
    @property
    def is_paid(self):
        return bool(self.stripe_subscription_id) and not self.is_trial