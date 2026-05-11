from celery import shared_task

from analytics_engine.models import (
    PaymentAnalytics
)

from global_payments.models import (
    SubscriptionPaymentTransaction
)


@shared_task
def create_payment_analytics(
    transaction_id
):

    payment_transaction = (
        SubscriptionPaymentTransaction.objects.get(
            id=transaction_id
        )
    )

    PaymentAnalytics.objects.create(

        transaction_id=str(
            payment_transaction.transaction_id
        ),

        payment_type=
        payment_transaction.payment_for,

        gateway=
        payment_transaction.gateway,

        amount=
        payment_transaction.amount,

        currency=
        payment_transaction.currency,

        status=
        payment_transaction.status,

        metadata=
        payment_transaction.metadata
    )