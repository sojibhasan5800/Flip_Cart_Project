
from global_payments.models import (
    SubscriptionPaymentTransaction
)


def create_payment_transaction(
    *,
    payment_for,
    amount,
    currency,
    gateway,
    gateway_transaction_id,
    status="pending",
    metadata=None,
    customer_email=None,
):

    metadata = metadata or {}

    existing_transaction = (
        SubscriptionPaymentTransaction.objects
        .select_for_update()
        .filter(
            gateway_transaction_id=
            gateway_transaction_id
        )
        .first()
    )

    if existing_transaction:
        return existing_transaction

    payment_transaction = (
        SubscriptionPaymentTransaction.objects.create(
            payment_for=payment_for,
            amount=amount,
            currency=currency,
            gateway=gateway,
            gateway_transaction_id=
            gateway_transaction_id,
            status=status,
            metadata=metadata,
            customer_email=customer_email,
        )
    )

    return payment_transaction