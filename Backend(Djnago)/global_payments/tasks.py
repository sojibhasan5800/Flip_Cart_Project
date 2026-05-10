# global_payments/tasks.py

from celery import shared_task
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from .models import (
    SubscriptionPaymentTransaction,
    Invoice
)

from billing.models import (
    OrganizationSubscription,
    CustomerSubscription,
    SubscriptionPlan
)

from merchant_user.models import Organization

import uuid
import logging

logger = logging.getLogger(__name__)

from celery import shared_task
from django.core.mail import send_mail

from global_payments.models import SubscriptionPaymentTransaction


@shared_task
def send_payment_success_email(transaction_id):

    payment_transaction = SubscriptionPaymentTransaction.objects.get(
        id=transaction_id
    )

    send_mail(
        subject="Payment Successful",
        message=f"""
        Your payment was successful.

        Transaction ID:
        {payment_transaction.transaction_id}

        Amount:
        {payment_transaction.amount}

        Thank you.
        """,
        from_email=None,
        recipient_list=[payment_transaction.customer_email],
        fail_silently=False
    )

@shared_task(
    bind=True,
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 5}
)
def process_successful_payment(self, transaction_id):

    try:

        with transaction.atomic():

            payment_transaction = (
                SubscriptionPaymentTransaction.objects
                .select_for_update()
                .get(id=transaction_id)
            )

            # =========================
            # IDEMPOTENCY PROTECTION
            # =========================

            if payment_transaction.is_verified:
                logger.info(
                    f"Payment already processed: {payment_transaction.id}"
                )
                return

            if payment_transaction.status != "success":
                logger.warning(
                    f"Payment not successful: {payment_transaction.id}"
                )
                return

            metadata = payment_transaction.metadata or {}

            plan_type = metadata.get("plan_type")

            # ==================================================
            # ORGANIZATION SUBSCRIPTION ACTIVATION
            # ==================================================

            if plan_type == "organization":

                activate_organization_subscription(
                    payment_transaction=payment_transaction,
                    metadata=metadata
                )

            # ==================================================
            # PRODUCT BOOST ACTIVATION
            # ==================================================

            elif plan_type == "product_boost":

                activate_product_boost_subscription(
                    payment_transaction=payment_transaction,
                    metadata=metadata
                )

            # ==================================================
            # CUSTOMER SUBSCRIPTION
            # ==================================================

            elif plan_type == "plus_membership":

                activate_customer_subscription(
                    payment_transaction=payment_transaction,
                    metadata=metadata
                )

            # ==================================================
            # GENERATE INVOICE
            # ==================================================

            invoice = generate_invoice(payment_transaction)

            # ==================================================
            # SEND EMAIL
            # ==================================================

            send_payment_success_email.delay(
                transaction_id=payment_transaction.id
            )

            # ==================================================
            # WEBSOCKET NOTIFY
            # ==================================================

            websocket_payment_notification.delay(
                transaction_id=payment_transaction.id
            )

            # ==================================================
            # ANALYTICS
            # ==================================================

            create_payment_analytics.delay(
                transaction_id=payment_transaction.id
            )

            # ==================================================
            # AUDIT LOG
            # ==================================================

            create_payment_audit_log.delay(
                transaction_id=payment_transaction.id
            )

            # ==================================================
            # MARK VERIFIED
            # ==================================================

            payment_transaction.is_verified = True
            payment_transaction.webhook_received_at = timezone.now()

            payment_transaction.save(
                update_fields=[
                    "is_verified",
                    "webhook_received_at"
                ]
            )

            logger.info(
                f"Payment fully processed: {payment_transaction.id}"
            )

    except Exception as e:

        logger.error(str(e))

        raise self.retry(exc=e)