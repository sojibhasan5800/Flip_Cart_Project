import stripe
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import Tenant

stripe.api_key = settings.STRIPE_SECRET_KEY

class StripeBillingService:
    @staticmethod
    def create_tenant_customer(tenant, token=None):
        """Create Stripe customer for tenant"""
        try:
            customer = stripe.Customer.create(
                email=tenant.email,
                name=tenant.name,
                metadata={
                    'tenant_id': str(tenant.id),
                    'subdomain': tenant.subdomain
                }
            )
            
            tenant.stripe_customer_id = customer.id
            tenant.save()
            
            return customer
        except stripe.error.StripeError as e:
            print(f"Stripe Error: {e}")
            return None

    @staticmethod
    def create_subscription(tenant, price_id, trial_days=14):
        """Create subscription with trial period"""
        try:
            if not tenant.stripe_customer_id:
                customer = StripeBillingService.create_tenant_customer(tenant)
                if not customer:
                    return None

            subscription = stripe.Subscription.create(
                customer=tenant.stripe_customer_id,
                items=[{'price': price_id}],
                trial_period_days=trial_days,
                metadata={
                    'tenant_id': str(tenant.id),
                    'subdomain': tenant.subdomain
                }
            )
            
            tenant.stripe_subscription_id = subscription.id
            tenant.is_trial = True
            tenant.trial_ends_at = timezone.now() + timedelta(days=trial_days)
            tenant.save()
            
            return subscription
        except stripe.error.StripeError as e:
            print(f"Stripe Subscription Error: {e}")
            return None

    @staticmethod
    def handle_webhook(event):
        """Handle Stripe webhook events"""
        if event['type'] == 'customer.subscription.updated':
            subscription = event['data']['object']
            try:
                tenant = Tenant.objects.get(stripe_subscription_id=subscription['id'])
                if subscription['status'] == 'active':
                    tenant.is_trial = False
                    tenant.save()
            except Tenant.DoesNotExist:
                pass
        
        elif event['type'] == 'customer.subscription.deleted':
            subscription = event['data']['object']
            try:
                tenant = Tenant.objects.get(stripe_subscription_id=subscription['id'])
                tenant.stripe_subscription_id = ''
                tenant.is_trial = True
                tenant.save()
            except Tenant.DoesNotExist:
                pass