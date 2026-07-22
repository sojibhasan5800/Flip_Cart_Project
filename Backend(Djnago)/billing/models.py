# billing/models.py (Extended from previous, added Invoice, more extensible fields)
from django.db import models
from django.utils import timezone
from django.conf import settings
from merchant_user.models import Organization
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
        ('product_boost', 'Product Boosting Add-on'),  # For product boosting
        ('plus_membership', 'plus_membership Plan'),  # For future extensions
    ]
    BILLING_CYCLE = [
        ("7_days", "7 Days"),
        ("15_days", "15 Days"),
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly (3 Months)"),
        ("half_yearly", "Half Yearly (6 Months)"),
        ("yearly", "Yearly"),
    ]

    
    name = models.CharField(max_length=100, unique=True)  # e.g., 'Basic', 'Pro Boost'
    slug = models.SlugField(max_length=100, unique=True)  # e.g., 'basic', 'pro-boost'
    plan_level = models.CharField(max_length=50, choices=PLAN_LEVELS, default='basic')
    plan_type = models.CharField(max_length=50, choices=PLAN_TYPES, default='general')
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)])
    currency = models.CharField(max_length=3, default='USD')
    billing_cycle = models.CharField(max_length=20, choices=BILLING_CYCLE, default='monthly')
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
    
    
    # --------------------------
    # Shipping Benefits
    # --------------------------
    free_shipping = models.BooleanField(default=False)

    free_shipping_min_order = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)]
    )

    max_free_shipping_orders = models.PositiveIntegerField(
        default=999999,
        help_text="Maximum free shipping orders during this subscription"
    )

    shipping_discount_percent = models.PositiveSmallIntegerField(
        default=0,
        help_text="0-100%"
    )

    # --------------------------
    # Order Benefits
    # --------------------------
    priority_order_processing = models.BooleanField(default=False)

    priority_customer_support = models.BooleanField(default=False)

    early_access_sale = models.BooleanField(default=False)

    exclusive_deals = models.BooleanField(default=False)

    cashback_percent = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=0
    )

    reward_points_multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=1.00
    )

    # --------------------------
    # Profit Protection
    # --------------------------
    monthly_order_limit = models.PositiveIntegerField(
        default=0,
        help_text="0 = Unlimited"
    )

    monthly_spending_limit = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text="0 = Unlimited"
    )

    # --------------------------
    # Priority
    # --------------------------
    display_order = models.PositiveIntegerField(
        default=0
    )

    recommended = models.BooleanField(default=False)

    badge = models.CharField(
        max_length=50,
        blank=True
    )

 
    
    

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

class CustomerSubscription(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('cancelled', 'Cancelled'),
        ('past_due', 'Past Due'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)

    stripe_subscription_id = models.CharField(max_length=100, unique=True)
    stripe_customer_id = models.CharField(max_length=100, blank=True)

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')

    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField(null=True, blank=True)

    auto_renew = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.plan.name}"

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
