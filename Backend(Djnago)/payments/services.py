# payments/services.py
from django_tenants.utils import schema_context
from django.db import transaction
from payments.models import PaymentTransaction
from .subscription_service import activate_organization_subscription, activate_boosting_subscription

def create_payment_transaction(org_schema,organization_id, subscription_id=None, boost_id=None,
                               amount=0, currency='USD', gateway='stripe',
                               gateway_transaction_id=None, status='pending',
                               metadata=None, customer_email=None, receipt_url=None, notes=None):
    """
    General service to create PaymentTransaction
    """
    metadata = metadata or {}
    with schema_context(org_schema):
        with transaction.atomic():
            existing = PaymentTransaction.objects.filter(
                gateway_transaction_id=gateway_transaction_id
            ).first()

            if existing:
                print("Duplicate transaction ignored")
                return existing
            trans = PaymentTransaction.objects.create(
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

def handle_payment_success(trans: PaymentTransaction):
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