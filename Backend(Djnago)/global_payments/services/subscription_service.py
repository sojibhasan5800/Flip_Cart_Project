

from datetime import timezone

from billing.models import OrganizationSubscription, SubscriptionPlan
from merchant_user.models import Organization


def activate_organization_subscription(
    payment_transaction,
    metadata
):

    org_id = metadata.get("org_id")
    plan_id = metadata.get("plan_id")

    organization = Organization.objects.get(id=org_id)

    plan = SubscriptionPlan.objects.get(
        id=plan_id,
        is_active=True
    )

    subscription, created = (
        OrganizationSubscription.objects.get_or_create(
            organization=organization,
            defaults={
                "plan": plan,
                "status": "active",
                "start_date": timezone.now(),
                "end_date": timezone.now() + timezone.timedelta(
                    days=plan.get_duration()
                )
            }
        )
    )

    if not created:

        subscription.plan = plan
        subscription.status = "active"
        subscription.start_date = timezone.now()
        subscription.end_date = (
            timezone.now() +
            timezone.timedelta(days=plan.get_duration())
        )

        subscription.save()

    payment_transaction.organization_subscription = subscription

    payment_transaction.save(
        update_fields=["organization_subscription"]
    )