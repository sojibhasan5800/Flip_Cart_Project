from django.db import models
from django.utils import timezone
from billing.models import OrganizationSubscription, ProductBoostSubscription, Invoice
from store.models import Product
from merchant_user.models import Organization
import uuid

class PaymentTransaction(models.Model):
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
    
    # Organization & subscription relation
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(OrganizationSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    boost = models.ForeignKey(ProductBoostSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    
     # Payment details
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    payment_method = models.CharField(max_length=50, blank=True, null=True, help_text="Card, bKash, Rocket etc.")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway_transaction_id = models.CharField(max_length=100, blank=True, unique=True)  # Stripe charge ID or bKash paymentID
   
    # Extra info
    metadata = models.JSONField(default=dict, blank=True, help_text="e.g., {'plan_type': 'organization', 'plan_id': 3, 'boost_product_id': 12}")
    customer_email = models.EmailField(blank=True, null=True)
    receipt_url = models.URLField(blank=True, null=True)
    refunded_at = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"

    def verify_and_complete(self):
        if self.status == 'success':
            # Create invoice
            Invoice.objects.create(
                organization=self.organization,
                subscription=self.subscription,
                amount=self.amount,
                status='paid' if self.status == 'success' else 'failed',
                line_items=[{'description': 'Product Boost' if self.boost else 'Subscription Payment', 'amount': self.amount}]
            )