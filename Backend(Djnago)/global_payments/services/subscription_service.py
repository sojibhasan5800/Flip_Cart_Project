

from django.utils import timezone
from datetime import timedelta
from importlib.metadata import metadata

from accounts.models import Account
from billing.models import OrganizationSubscription, SubscriptionPlan,ProductBoostSubscription,CustomerSubscription
from merchant_user.models import Organization



def activate_organization_subscription(
    payment_transaction,
    metadata
):

    org_id = metadata.get("org_id")
    plan_id = metadata.get("plan_id")
    stripe_subscription_id = metadata.get(
    "stripe_subscription_id"
    )

    stripe_customer_id = metadata.get(
        "stripe_customer_id"
    )

    stripe_subscription_item_id = metadata.get(
        "stripe_subscription_item_id"
    )

    organization = Organization.objects.select_for_update().get(id=org_id)

    plan = SubscriptionPlan.objects.get(
        id=plan_id,
        is_active=True
    )
    
    old_subscription = (
    OrganizationSubscription.objects
    .filter(
        organization=organization,
        status="active"
    )
    .first()
    )
    
    if old_subscription:

        old_subscription.status = "expired"

        old_subscription.save(
            update_fields=["status"]
        )
        
    subscription = (
    OrganizationSubscription.objects.create(

        organization=organization,

        plan=plan,

        status="active",

        start_date=timezone.now(),

        end_date=timezone.now() +
        timedelta(days=plan.get_duration()),

        stripe_subscription_id=
        stripe_subscription_id,

        stripe_customer_id=
        stripe_customer_id,

        stripe_subscription_item_id=
        stripe_subscription_item_id,
        )
    )

    payment_transaction.organization_subscription = subscription

    payment_transaction.save(
        update_fields=["organization_subscription"]
    )
    
    


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
            timedelta(
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


def activate_customer_subscription(
    payment_transaction,
    metadata
):

    user_id = metadata.get("user_id")

    plan_id = metadata.get("plan_id")

    stripe_subscription_id = metadata.get(
        "stripe_subscription_id"
    )

    stripe_customer_id = metadata.get(
        "stripe_customer_id"
    )

    user = Account.objects.select_for_update().get(
        id=user_id
    )

    plan = SubscriptionPlan.objects.get(
        id=plan_id,
        is_active=True
    )

    subscription, created = (
        CustomerSubscription.objects.get_or_create(

            user=user,

            defaults={

                "plan": plan,

                "stripe_subscription_id":
                stripe_subscription_id,

                "stripe_customer_id":
                stripe_customer_id,

                "status": "active",

                "start_date":
                timezone.now(),

                "end_date":
                timezone.now() +
                timezone.timedelta(
                    days=plan.get_duration()
                ),

                "auto_renew": True
            }
        )
    )

    # =========================
    # UPDATE EXISTING SUB
    # =========================

    if not created:

        subscription.plan = plan

        subscription.status = "active"

        subscription.stripe_subscription_id = (
            stripe_subscription_id
        )

        subscription.stripe_customer_id = (
            stripe_customer_id
        )

        subscription.start_date = (
            timezone.now()
        )

        subscription.end_date = (
            timezone.now() +
            timedelta(
                days=plan.get_duration()
            )
        )

        subscription.auto_renew = True

        subscription.save()

    # =========================
    # LINK PAYMENT TRANSACTION
    # =========================

    payment_transaction.customer_subscription = (
        subscription
    )

    payment_transaction.save(
        update_fields=[
            "customer_subscription"
        ]
    )

    return subscription