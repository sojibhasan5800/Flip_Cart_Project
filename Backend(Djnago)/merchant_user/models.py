from typing import Required
from django.db import models
import uuid
from django_tenants.models import TenantMixin, DomainMixin
from django.conf import settings
from django.utils import timezone

class Organization(TenantMixin):
    """
    প্রতিটি ই-কমার্স দোকান/ব্যবসা একটি Organization (Tenant)
    প্রতিটির নিজস্ব isolated database schema থাকবে
    """
    # id = models.BigAutoField(primary_key=True)        # default auto increment
    # org_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    username = models.CharField(max_length=100, unique=True)
    business_name = models.CharField(max_length=200, help_text="Organization/Company Name")
    store_logo = models.URLField(
        blank=True,
        null=True,
        help_text="ImageKit hosted store logo URL"
        )
    
    # Tenant specific fields (django-tenants requires these)
    schema_name = models.CharField(max_length=63, unique=True, blank=True)
    duplicate_schema_name = models.CharField(max_length=100, blank=True)  # Organization name (duplicate for django-tenants)
    
    # Business Information
    business_email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20)
    website = models.URLField(blank=True)
    store_description = models.CharField(max_length=500, blank=True)
    
    # Business Details
    business_type = models.CharField(max_length=100, choices=[ 
        ('retail', 'Retail Store'),
        ('wholesale', 'Wholesale Business'),
        ('manufacturer', 'Manufacturer'),
        ('service', 'Service Provider'),
        ('dropshipping', 'Dropshipping'),
        ('other', 'Other'),
    ], default='retail')
    
    # Address
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True, default='Dhaka')
    state = models.CharField(max_length=100, blank=True, default='Dhaka Division')
    postal_code = models.CharField(max_length=20, blank=True, default='1206')
    country = models.CharField(max_length=100, blank=True, default='Bangladesh')
    
    # Subscription & Billing (Stripe)
    subscription_plan = models.CharField(max_length=50, choices=[
        ('free_trial', 'Free Trial'),
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('premium', 'Premium'),
        ('enterprise', 'Enterprise'),
    ], default='free_trial')
    
    subscription_status = models.CharField(max_length=50, choices=[
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('suspended', 'Suspended'),
        ('cancelled', 'Cancelled'),
    ], default='active')
    
    stripe_customer_id = models.CharField(max_length=100, blank=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    
    # Trial Information
    is_trial = models.BooleanField(default=True)
    trial_ends_at = models.DateTimeField(null=True, blank=True)
    
    # Features & Limits
    max_users = models.PositiveIntegerField(default=5)
    max_products = models.PositiveIntegerField(default=100)
    max_storage_gb = models.PositiveIntegerField(default=1)
    max_monthly_orders = models.PositiveIntegerField(default=1000)
    
    # Status Flags
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_suspended = models.BooleanField(default=False)
    
    # Delivery Integration
    delivery_integration = models.CharField(max_length=50, choices=[
        ('internal', 'Internal Delivery System'),
        ('external', 'External Courier Service'),
        ('both', 'Both Internal & External'),
        ('none', 'No Delivery'),
    ], default='internal')
    
    # Tenant settings (django-tenants)
    auto_create_schema = True
    auto_drop_schema = False
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    onboarded_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Organization"
        verbose_name_plural = "Organizations"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.business_name} ({self.schema_name})"

    
    def save(self, *args, **kwargs):
        # Generate schema_name if not provided
        if not self.schema_name:
            self.schema_name = self.generate_schema_name()
        super().save(*args, **kwargs)

    
    
    def generate_schema_name(self):
        """Generate unique schema name"""
        import re
        import time
        # Clean name for schema
        clean_name = re.sub(r'[^a-z0-9]', '', self.business_name.lower())
        timestamp = str(int(time.time()))[-6:]
        return f"{clean_name[:40]}_{timestamp}"
    
    @property
    def is_paid(self):
        """Check if organization has paid subscription"""
        if self.is_trial:
            return False
        return bool(self.stripe_subscription_id) and self.subscription_status == 'active'
    
    @property
    def days_remaining_in_trial(self):
        """Days remaining in trial period"""
        if not self.is_trial or not self.trial_ends_at:
            return 0
        remaining = self.trial_ends_at - timezone.now()
        return max(0, remaining.days)
    
    @property
    def store_url(self):
        """Get store URL safely, with default to https if USE_SSL not set"""
        primary_domain = self.domains.filter(is_primary=True).first()
        if primary_domain:
            # settings এ USE_SSL থাকলে তা ব্যবহার করবে, না থাকলে True ধরে নেবে
            use_ssl = getattr(settings, "USE_SSL", True)
            protocol = 'https' if use_ssl else 'http'
            return f"{protocol}://{primary_domain.domain}"
        return None

    
    def has_delivery_integration(self):
        """Check if organization has delivery integration"""
        return self.delivery_integration in ['internal', 'both']


class OrganizationDomain(DomainMixin):
    """
    Organization-এর ডোমেইন/সাবডোমেইন ম্যাপিং
    """
    tenant = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='domains'
    )
    
    # Additional fields
    domain_type = models.CharField(max_length=20, choices=[
        ('primary', 'Primary Domain'),
        ('alias', 'Domain Alias'),
        ('development', 'Development'),
        ('staging', 'Staging'),
    ], default='primary')
    
    # SSL Configuration
    ssl_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('error', 'Error'),
    ], default='pending')
    
    ssl_certificate = models.TextField(blank=True)
    ssl_private_key = models.TextField(blank=True)
    ssl_expiry_date = models.DateField(null=True, blank=True)
    
    # Verification
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)
    
    # DNS Records
    a_record = models.CharField(max_length=100, blank=True)
    cname_record = models.CharField(max_length=100, blank=True)
    txt_record = models.CharField(max_length=500, blank=True)
    
    # Analytics
    google_site_verification = models.CharField(max_length=100, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Organization Domain"
        verbose_name_plural = "Organization Domains"
        unique_together = ['tenant', 'domain']
    
    def save(self, *args, **kwargs):
        # Ensure only one primary domain per tenant
        if self.is_primary:
            OrganizationDomain.objects.filter(
                tenant=self.tenant,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.domain} → {self.tenant.business_name} ({self.tenant.schema_name})"


class MerchantUser(models.Model):
    """
    Organization-এর ইউজার (অ্যাডমিন, ম্যানেজার, স্টাফ)
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('admin', 'Administrator'),
        ('manager', 'Manager'),
        ('staff', 'Staff'),
        ('delivery_manager', 'Delivery Manager'),
        ('customer_support', 'Customer Support'),
        ('viewer', 'Viewer'),
    ]
    
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='merchant_users'
    )
    
    user = models.ForeignKey(
        'accounts.Account',
        on_delete=models.CASCADE,
        related_name='merchant_profile'
    )
    
    role = models.CharField(max_length=50, choices=ROLE_CHOICES, default='staff')
    
    # Department & Designation
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    employee_id = models.CharField(max_length=50, blank=True)
    
    # Permissions (JSON field for flexible permissions)
    permissions = models.JSONField(default=dict, blank=True)
    
    # Contact Information
    work_email = models.EmailField(blank=True)
    work_phone = models.CharField(max_length=20, blank=True)
    emergency_contact = models.CharField(max_length=20, blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    can_login_admin = models.BooleanField(default=True)
    
    # Security
    two_factor_enabled = models.BooleanField(default=False)
    last_password_change = models.DateTimeField(null=True, blank=True)
    
    # Activity Tracking
    last_login_at = models.DateTimeField(null=True, blank=True)
    last_activity_at = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    joined_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Merchant User"
        verbose_name_plural = "Merchant Users"
        unique_together = ['organization', 'user']
        ordering = ['-joined_at']
    
    def __str__(self):
        return f"{self.user.email} - {self.organization.business_name} ({self.role})"
    
    @property
    def full_name(self):
        return self.user.get_full_name()
    
    def has_permission(self, permission_code):
        """Check if user has specific permission"""
        if self.role in ['owner', 'admin']:
            return True
        return permission_code in self.permissions.get('allowed', [])
    
    def get_role_permissions(self):
        """Get default permissions based on role"""
        role_permissions = {
            'owner': ['all'],
            'admin': ['manage_store', 'manage_products', 'manage_orders', 
                     'manage_customers', 'manage_delivery', 'manage_staff',
                     'view_reports', 'manage_settings'],
            'manager': ['manage_products', 'manage_orders', 'manage_delivery'],
            'staff': ['view_orders', 'update_order_status'],
            'delivery_manager': ['manage_delivery', 'assign_delivery_boy'],
            'customer_support': ['manage_customers', 'view_orders'],
            'viewer': ['view_reports'],
        }
        return role_permissions.get(self.role, [])