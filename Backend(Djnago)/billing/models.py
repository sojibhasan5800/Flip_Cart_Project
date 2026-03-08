# billing/models.py (Extended from previous, added Invoice, more extensible fields)
from django.db import models
from django.utils import timezone
from django.conf import settings
from merchant_user.models import Organization
# from store.models import Product
import uuid
from django.core.validators import MinValueValidator

class SubscriptionPlan(models.Model):
    """
    Extensible model for subscription plans. Use JSONField for features to allow easy addition of new attributes.
    Supports Basic, Pro, Enterprise out-of-the-box, but can add more via admin.
    """
    PLAN_LEVELS = [
        ('basic', 'Basic'),
        # ('pro', 'Pro'),
        ('premium', 'Premium'),
        ('standard', 'Standard'),
        ('enterprise', 'Enterprise'),
    ]
    PLAN_TYPES = [
        ('general', 'General Store Plan'),
        ('organization', 'Organization-wide Plan'),  # For future use if needed
        ('boosting', 'Product Boosting Add-on'),  # For product boosting
        ('custom', 'Custom Plan'),  # For future extensions
    ]
    
    name = models.CharField(max_length=100, unique=True)  # e.g., 'Basic', 'Pro Boost'
    slug = models.SlugField(max_length=100, unique=True)  # e.g., 'basic', 'pro-boost'
    plan_level = models.CharField(max_length=50, choices=PLAN_LEVELS, default='basic')
    plan_type = models.CharField(max_length=50, choices=PLAN_TYPES, default='general')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)])
    currency = models.CharField(max_length=3, default='USD')
    billing_cycle = models.CharField(max_length=20, choices=[('monthly', 'Monthly'), ('yearly', 'Yearly')], default='monthly')
    duration_days = models.PositiveIntegerField(default=30)  # Flexible for different cycles
    max_users = models.PositiveIntegerField(default=1, help_text="Max users per organization")
    max_products = models.PositiveIntegerField(default=100, help_text="Max products in store")
    max_boosted_products = models.PositiveIntegerField(default=0, help_text="Max boosted products (for boosting plans)")
    storage_gb = models.PositiveIntegerField(default=5, help_text="Storage limit in GB")
    features = models.JSONField(default=dict, help_text="JSON of features, e.g., {'analytics': true, 'priority_support': true}")  # Extensible
    stripe_price_id = models.CharField(max_length=100, blank=True)  # For Stripe
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        ordering = ['plan_level', 'price']

    def __str__(self):
        return f"{self.name} ({self.plan_level} - {self.plan_type})"

    def get_duration(self):
        """Calculate duration based on billing_cycle for future extensibility"""
        if self.billing_cycle == 'yearly':
            return 365
        return self.duration_days

class OrganizationSubscription(models.Model):
    """
    Tracks merchant (organization) subscriptions. Supports multiple active subs (e.g., general + boosting add-on).
    Lifecycle managed via Stripe signals/tasks.
    """
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('past_due', 'Past Due'),
        ('unpaid', 'Unpaid'),
        ('cancelled', 'Cancelled'),
        ('incomplete', 'Incomplete'),
        ('expired', 'Expired'),
    ]
    
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name='org_subscriptions')
    start_date = models.DateTimeField(default=timezone.now,db_index=True)
    end_date = models.DateTimeField(null=True, blank=True,db_index=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active',db_index=True)
    stripe_subscription_id = models.CharField(max_length=100, blank=True, unique=True)
    stripe_subscription_item_id = models.CharField(max_length=255, blank=True, null=True) 
    stripe_customer_id = models.CharField(max_length=100, blank=True) 
    is_expiring_soon = models.BooleanField(default=False, db_index=True)
    current_usage = models.JSONField(default=dict, help_text="Track usage like {'products': 50, 'boosted': 2}")  # Extensible tracking
    boosted_products_count = models.PositiveIntegerField(default=0)  # Specific for boosting
    auto_renew = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    cancel_at_period_end = models.BooleanField(default=False)
    pending_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True,blank=True,related_name='pending_subscriptions')
    change_type = models.CharField(max_length=20, choices=[('upgrade', 'Upgrade'), ('downgrade', 'Downgrade')], null=True, blank=True)
    scheduled_change_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ['organization', 'stripe_subscription_id']
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['status', 'end_date']),
            models.Index(fields=['is_expiring_soon', 'end_date']),
        ]

    def __str__(self):
        return f"{self.organization.business_name} - {self.plan.name} ({self.status})"

    def save(self, *args, **kwargs):        
            super().save(*args, **kwargs)

    def is_active(self):
        return self.status == 'active' and (self.end_date is None or self.end_date > timezone.now())

    def can_boost_more(self):
        return self.boosted_products_count < self.plan.max_boosted_products

    def upgrade_plan(self, new_plan,update_type):
        """Logic for upgrade/downgrade - prorate if needed"""
        if update_type == 'upgrade':
            print(f"Upgrading subscription for {self.organization.business_name} from {self.plan.name} to {new_plan.name}")
            # Upgrade: immediate effect, prorate remaining
            self.plan = new_plan
            self.start_date = timezone.now()
            self.end_date = self.start_date + timezone.timedelta(days=new_plan.get_duration())
            self.status = 'active'
            self.save()
            # Trigger Stripe update via task
            # from .tasks import update_stripe_subscription
            # update_stripe_subscription.delay(self.id)
        elif update_type == 'downgrade':
            # Downgrade: effective at end of current period
            self.status = 'active'  # Keep active till end
            # Schedule downgrade
            # from .tasks import schedule_downgrade
            # schedule_downgrade.delay(self.id, new_plan.id)

class ProductBoostSubscription(models.Model):
    """
    Per-product boosting, linked to org subscription. Extensible for different boost levels.
    """
    BOOST_LEVELS = [
        (1, 'Standard'),
        (2, 'Premium'),
        (3, 'VIP'),
    ]
    
    # product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='boosts')
    organization_subscription = models.ForeignKey(OrganizationSubscription, on_delete=models.CASCADE, related_name='product_boosts')
    boost_start_date = models.DateTimeField(default=timezone.now)
    boost_end_date = models.DateTimeField()
    priority_level = models.PositiveIntegerField(choices=BOOST_LEVELS, default=1)
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict, help_text="Extra data for future features, e.g., {'ad_placement': 'top_feed'}")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority_level', '-boost_start_date']

    def __str__(self):
        return f"Boost {self.get_priority_level_display()} for {self.organization_subscription.organization.business_name}"
        # return f"Boost {self.get_priority_level_display()} for {self.product.product_name}"

    def save(self, *args, **kwargs):
        if not self.boost_end_date:
            self.boost_end_date = self.boost_start_date + timezone.timedelta(days=30)  # Default, can override based on plan
        super().save(*args, **kwargs)
        # Sync to Redis for fast feed
        # from .tasks import sync_boosted_product_to_redis
        # sync_boosted_product_to_redis.delay(self.product.id, self.product.organization.schema_name)
        # # Update org sub count
        # self.organization_subscription.boosted_products_count = self.organization_subscription.product_boosts.filter(is_active=True).count()
        # self.organization_subscription.save()


class SubscriptionHistory(models.Model):
    subscription = models.ForeignKey(
        'OrganizationSubscription',
        on_delete=models.CASCADE,
        related_name='history'
    )
    old_plan = models.ForeignKey(
        'SubscriptionPlan',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    new_plan = models.ForeignKey(
        'SubscriptionPlan',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='+'
    )
    change_type = models.CharField(max_length=20, choices=[
        ('upgrade', 'Upgrade'),
        ('downgrade', 'Downgrade'),
        ('cancel', 'Cancel'),
        ('renew', 'Renew'),
    ])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subscription.organization.business_name}: {self.change_type} {self.old_plan} → {self.new_plan}"



class Invoice(models.Model):
    """
    Invoice generation model. Supports PDF generation via tasks/views.
    Extensible with line items JSON.
    """
    invoice_number = models.CharField(max_length=50, unique=True, default=uuid.uuid4)
    organization = models.ForeignKey(Organization, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    subscription = models.ForeignKey(OrganizationSubscription, on_delete=models.SET_NULL, null=True, blank=True, related_name='invoices')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    status = models.CharField(max_length=20, choices=[('paid', 'Paid'), ('pending', 'Pending'), ('failed', 'Failed')], default='pending')
    stripe_invoice_id = models.CharField(max_length=100, blank=True)
    pdf_url = models.URLField(blank=True, help_text="Generated PDF URL, e.g., via Cloudinary")
    line_items = models.JSONField(default=list, help_text="List of items, e.g., [{'description': 'Basic Plan', 'amount': 19.99}]")
    issued_at = models.DateTimeField(default=timezone.now)
    due_at = models.DateTimeField()
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issued_at']

    def __str__(self):
        return f"Invoice {self.invoice_number} for {self.organization.business_name}"

    def save(self, *args, **kwargs):
        if not self.due_at:
            self.due_at = self.issued_at + timezone.timedelta(days=14)
        super().save(*args, **kwargs)
        # Generate PDF async
        # from .tasks import generate_invoice_pdf
        # generate_invoice_pdf.delay(self.id)