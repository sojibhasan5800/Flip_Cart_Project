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
    
    transaction_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='payments')
    subscription = models.ForeignKey(OrganizationSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    boost = models.ForeignKey(ProductBoostSubscription, on_delete=models.SET_NULL, null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    gateway = models.CharField(max_length=20, choices=GATEWAY_CHOICES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    gateway_transaction_id = models.CharField(max_length=100, blank=True)  # Stripe charge ID or bKash paymentID
    metadata = models.JSONField(default=dict)  # Extra data, e.g., {'boost_product_id': 123}
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_id} - {self.status}"

    def verify_and_complete(self):
        if self.status == 'success':
            # Link to billing: create boost or update sub
            if 'boost_product_id' in self.metadata:
                product = Product.objects.get(id=self.metadata['boost_product_id'])
                boost = ProductBoostSubscription.objects.create(
                    product=product,
                    organization_subscription=self.subscription,
                    boost_end_date=timezone.now() + timezone.timedelta(days=30),  # From plan
                    priority_level=1  # Default
                )
                product.is_boosted = True
                product.save()
                # Sync Redis
                from billing.tasks import sync_boosted_product_to_redis
                sync_boosted_product_to_redis.delay(product.id, product.organization.schema_name)
            # Create invoice
            Invoice.objects.create(
                organization=self.organization,
                subscription=self.subscription,
                amount=self.amount,
                status='paid' if self.status == 'success' else 'failed',
                line_items=[{'description': 'Product Boost' if self.boost else 'Subscription Payment', 'amount': self.amount}]
            )