
# payments/services.py
from django_tenants.utils import schema_context
from django.db import transaction
from .models import SubscriptionPaymentTransaction
from .subscription_service import activate_organization_subscription, activate_boosting_subscription


# transaction_service.py

from django.db import transaction
from django.utils import timezone

from global_payments.models import SubscriptionPaymentTransaction


def create_payment_transaction(
    *,
    payment_for,
    amount,
    currency,
    gateway,
    gateway_transaction_id,
    status='pending',
    metadata=None,
    customer_email=None,
    organization_subscription=None,
    customer_subscription=None,
    product_boost_subscription=None,
):

    metadata = metadata or {}

    with transaction.atomic():

        existing_transaction = (
            SubscriptionPaymentTransaction.objects
            .select_for_update()
            .filter(
                gateway_transaction_id=gateway_transaction_id
            )
            .first()
        )

        # Idempotency protection
        if existing_transaction:
            return existing_transaction

        transaction_obj = SubscriptionPaymentTransaction.objects.create(
            payment_for=payment_for,
            amount=amount,
            currency=currency,
            gateway=gateway,
            gateway_transaction_id=gateway_transaction_id,
            status=status,
            metadata=metadata,
            customer_email=customer_email,
            organization_subscription=organization_subscription,
            customer_subscription=customer_subscription,
            product_boost_subscription=product_boost_subscription,
            paid_at=timezone.now() if status == 'success' else None
        )

    return transaction_obj


def create_payment_transaction(org_schema=None,organization_id=None, subscription_id=None, boost_id=None,
                               amount=0, currency='USD', gateway='stripe',
                               gateway_transaction_id=None, status='pending',
                               metadata=None, customer_email=None, receipt_url=None, notes=None):
    """
    General service to create PaymentTransaction
    """
    metadata = metadata or {}
    with schema_context(org_schema):
        with transaction.atomic():
            existing = SubscriptionPaymentTransaction.objects.filter(
                gateway_transaction_id=gateway_transaction_id
            ).first()

            if existing:
                print("Duplicate transaction ignored")
                return existing
            trans = SubscriptionPaymentTransaction.objects.create(
                organization_id=organization_id,
                subscription_id=subscription_id,
                boost_id=boost_id,
                amount=amount,
                currency=currency,
                gateway=gateway,
                gateway_transaction_id=gateway_transaction_id,
                status=status,
                metadata=metadata,
                customer_email=customer_email,
                receipt_url=receipt_url,
                notes=notes
            )
            print(f"PaymentTransaction created with ID: {trans.id}")
            # Only for successful payment, call post actions
            if status == 'success':
                handle_payment_success(trans)

    return trans

def handle_payment_success(trans: SubscriptionPaymentTransaction):
    """
    Central place for post-payment actions
    """
    # 🔹 Activate subscription or boost depending on metadata
    plan_type = trans.metadata.get('plan_type')

    if plan_type == 'organization':
        activate_organization_subscription(
            plan_id=trans.metadata.get('plan_id'),
            org_id=trans.organization_id,
            metadata = trans.metadata,
            session={'customer_gateway_id': trans.gateway_transaction_id}


        )
    elif plan_type == 'boosting':
        activate_boosting_subscription(
            plan_id=trans.metadata.get('plan_id'),
            org_id=trans.organization_id,
            metadata = trans.metadata,
            session={'id': trans.gateway_transaction_id}
        )

    # 🔹 Create invoice
    trans.verify_and_complete()