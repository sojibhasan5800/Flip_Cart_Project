

from datetime import timezone
from django.db import transaction

from billing.models import OrganizationSubscription, SubscriptionPlan,ProductBoostSubscription
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
    
    

@transaction.atomic
def activate_product_boost_subscription(
    payment_transaction,
    metadata
):

    org_id = metadata.get("org_id")

    plan_id = metadata.get("plan_id")

    priority_level = metadata.get(
        "priority_level",
        1
    )

    organization = (
        Organization.objects.select_for_update().get(
            id=org_id
        )
    )

    plan = SubscriptionPlan.objects.get(
        id=plan_id,
        is_active=True
    )

    organization_subscription = (
        OrganizationSubscription.objects.filter(
            organization=organization,
            status="active"
        )
        .select_related("plan")
        .first()
    )

    if not organization_subscription:

        raise Exception(
            "Active organization subscription not found"
        )

    # =========================
    # CHECK BOOST LIMIT
    # =========================

    active_boost_count = (
        ProductBoostSubscription.objects.filter(
            organization_subscription=
            organization_subscription,

            is_active=True
        ).count()
    )

    if (
        active_boost_count >=
        organization_subscription.plan.max_boosted_products
    ):

        raise Exception(
            "Boost limit exceeded"
        )

    # =========================
    # CREATE BOOST
    # =========================

    boost_subscription = (
        ProductBoostSubscription.objects.create(

            organization_subscription=
            organization_subscription,

            priority_level=
            priority_level,

            boost_start_date=
            timezone.now(),

            boost_end_date=
            timezone.now() +
            timezone.timedelta(
                days=plan.get_duration()
            ),

            metadata={
                "plan_id": plan.id,
                "plan_name": plan.name,
                **metadata
            }
        )
    )

    # =========================
    # UPDATE ORG SUB COUNT
    # =========================

    organization_subscription.boosted_products_count = (
        active_boost_count + 1
    )

    organization_subscription.save(
        update_fields=[
            "boosted_products_count"
        ]
    )

    # =========================
    # LINK PAYMENT TRANSACTION
    # =========================

    payment_transaction.productboost_subscription = (
        boost_subscription
    )

    payment_transaction.save(
        update_fields=[
            "productboost_subscription"
        ]
    )

    return boost_subscription