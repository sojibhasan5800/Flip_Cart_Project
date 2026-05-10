from django.db import models
from billing.models import OrganizationSubscription, ProductBoostSubscription, CustomerSubscription
import uuid




class SubscriptionPaymentTransaction(models.Model):
    
    SUBSCRIPTION_PAYMENT_TYPE_CHOICES = [
        ('organization', 'Organization'),
        ('product_boost', 'Product Boost'),
        ('plus_membership', 'Plus Membership'),
    ]
        
    GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('bkash', 'bKash'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]
    
    # Unique transaction ID
    transaction_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    
    # Ownership_subscription
    customer_subscription = models.ForeignKey(CustomerSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    organization_subscription = models.ForeignKey(OrganizationSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    productboost_subscription = models.ForeignKey(ProductBoostSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    
     # Type
    payment_type = models.CharField(max_length=20, choices=SUBSCRIPTION_PAYMENT_TYPE_CHOICES)
    
    # Financials
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')


     # Gateway
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    payment_method = models.CharField(max_length=50, blank=True, null=True, help_text="Card, bKash, Rocket etc.")
    gateway_transaction_id = models.CharField(max_length=100, blank=True, unique=True)  # Stripe charge ID or bKash paymentID
    
    #  Status
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
   
    # Extra info
    metadata = models.JSONField(default=dict, blank=True, help_text="Dynamic data based on payment type")
    customer_email = models.EmailField(blank=True, null=True)
    receipt_url = models.URLField(blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    #  Time
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"

    def verify_subscription_invoice_complete(self):
        if self.status == 'success':
            # Create invoice
            Invoice.objects.create(
                organization=self.organization,
                subscription=self.subscription,
                amount=self.amount,
                status='paid' if self.status == 'success' else 'failed',
                line_items=[{'description': 'Product Boost' if self.boost else 'Subscription Payment', 'amount': self.amount}]
            )

from django.db import models
import uuid


# =========================
# 1. PAYMENT TRANSACTION
# =========================
class SubscriptionPaymentTransaction(models.Model):

    PAYMENT_TYPE_CHOICES = [
        ('organization', 'Organization-wide Plan'),
        ('product_boost', 'Product Boosting Add-on'),
        ('plus_membership', 'Plus Membership Plan'),
    ]

    STATUS_CHOICES = [
        ('initiated', 'Initiated'),
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]

    GATEWAY_CHOICES = [
        ('stripe', 'Stripe'),
        ('bkash', 'bKash'),
    ]

    transaction_id = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    
    payment_for = models.CharField(max_length=50)
    organization_subscription = models.ForeignKey(
        OrganizationSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    plus_membership_subscription = models.ForeignKey(
        CustomerSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    product_boost_subscription = models.ForeignKey(
        ProductBoostSubscription,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )
    

    payment_type = models.CharField(
        max_length=30,
        choices=PAYMENT_TYPE_CHOICES
    )

    gateway = models.CharField(
        max_length=20,
        choices=GATEWAY_CHOICES
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='initiated'
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    currency = models.CharField(
        max_length=10,
        default='BDT'
    )

    gateway_transaction_id = models.CharField(
        max_length=200,
        blank=True,
        null=True
    )
    
    gateway_payment_intent_id = models.CharField(
        max_length=255,
        null=True,
        blank=True
    )

    customer_email = models.EmailField(
        blank=True,
        null=True
    )

    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Dynamic data based on payment type"
    )
    is_verified = models.BooleanField(default=False)
    
    paid_at = models.DateTimeField(null=True, blank=True)
    failure_reason = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            models.Index(fields=['gateway_transaction_id']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.transaction_id} - {self.status}"




# =========================
# 2. INVOICE MODEL
# =========================
class Invoice(models.Model):

    STATUS_CHOICES = [('paid', 'Paid'), ('failed', 'Failed'), ('refunded', 'Refunded')]

    transaction = models.OneToOneField(SubscriptionPaymentTransaction, on_delete=models.CASCADE, related_name='invoice')
    invoice_number = models.CharField(max_length=120, unique=True)
    payment_type = models.CharField(max_length=30)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    line_items = models.JSONField(default=list, blank=True, help_text="Breakdown of invoice items")
    metadata = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.invoice_number} - {self.status}"

    class Meta:
        ordering = ['-created_at']
        

# =========================
# 3. PAYMENT AUDIT LOG MODEL
# =========================

class PaymentAuditLog(models.Model):

    transaction = models.ForeignKey(
        SubscriptionPaymentTransaction,
        on_delete=models.CASCADE
    )

    event = models.CharField(max_length=255)

    metadata = models.JSONField(default=dict)

    created_at = models.DateTimeField(
        auto_now_add=True
    )