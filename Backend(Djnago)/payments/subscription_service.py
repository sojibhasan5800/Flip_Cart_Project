
from turtle import update

from django.utils import timezone
from django.db import transaction
from billing.models import OrganizationSubscription, SubscriptionPlan
from django_tenants.utils import schema_context, get_public_schema_name
from merchant_user.models import Organization
from django.core.exceptions import ObjectDoesNotExist

def activate_organization_subscription(plan_id, org_id, session):
    public_schema = get_public_schema_name()

    with schema_context(public_schema):
             
        plan = SubscriptionPlan.objects.get(id=plan_id)
        org = Organization.objects.get(id=org_id)
        now = timezone.now()

        with transaction.atomic():
            # চেক Active subscription
            active_subs = OrganizationSubscription.objects.filter(
                organization_id=org_id,
                status="active"
            ).order_by('-end_date')

            if active_subs.exists():
                current_sub = active_subs.first()
                # নতুন subscription শুরু হবে পুরানো শেষের পর থেকে
                start_date = max(current_sub.end_date, now)
            else:
                current_sub = None
                start_date = now
            end_date = start_date + timezone.timedelta(days=plan.get_duration())

            # OrganizationSubscription create/update
            org_sub, created = OrganizationSubscription.objects.update_or_create(
                    organization_id=org_id,
                    plan_id=plan_id,
                    defaults={
                        "start_date": start_date,
                        "end_date": end_date,
                        "status": "active",
                        "stripe_subscription_id": session.get("stripe_subscription_id", ""),
                        "stripe_customer_id": org.stripe_customer_id or session.get("stripe_customer_id", ""),
                    }
                )

            # Update organization subscription fields
            org.subscription_current_period_start = start_date
            org.subscription_current_period_end = end_date
            org.subscription_status = 'active'
            org.save(update_fields=[
                'subscription_current_period_start',
                'subscription_current_period_end',
                'subscription_status'
                ])
            return org_sub

def activate_boosting_subscription(plan_id, org_id, session):
    plan = SubscriptionPlan.objects.get(id=plan_id)
    public_schema = get_public_schema_name()
    with schema_context(public_schema): 
        with transaction.atomic():
            sub = OrganizationSubscription.objects.get(
                organization_id=org_id,
                status="active"
            )
            sub.boosted_products_count  += plan.max_boosted_products
            sub.save()