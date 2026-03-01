
from django.utils import timezone
from django.db import transaction
from billing.models import OrganizationSubscription, SubscriptionPlan
from django_tenants.utils import schema_context, get_public_schema_name


def activate_organization_subscription(plan_id, org_id, session):
    plan = SubscriptionPlan.objects.get(id=plan_id)
    public_schema = get_public_schema_name()
    with schema_context(public_schema): 
        with transaction.atomic():
            OrganizationSubscription.objects.update_or_create(
                organization_id=org_id,
                defaults={
                    "plan": plan,
                    "status": "active",
                    "start_date": timezone.now(),
                    "end_date": timezone.now() + timezone.timedelta(days=plan.get_duration()),
                    # "payment_reference": session["id"]
                }
            )

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