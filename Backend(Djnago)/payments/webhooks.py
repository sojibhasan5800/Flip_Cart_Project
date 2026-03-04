# billing/webhooks.py
from django.utils import timezone
import stripe
from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from billing.models import OrganizationSubscription, SubscriptionPlan
from merchant_user.models import Organization

stripe.api_key = settings.STRIPE_SECRET_KEY


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        # 🔥 Select correct webhook secret
        webhook_secret = self.get_webhook_secret()

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=webhook_secret
            )
        except stripe.error.SignatureVerificationError:
            return HttpResponse("Invalid signature", status=400)
        except ValueError:
            return HttpResponse("Invalid payload", status=400)

        # ✅ Handle Stripe events
        if event["type"] == "checkout.session.completed":
            try:
                self.handle_checkout_completed(event["data"]["object"])
            except Exception as e:
                print("Webhook processing failed:", str(e))
                return HttpResponse("Processing error", status=500)
                # ✅ 2. Subscription Updated (Upgrade / Cancel at period end)
        elif event["type"] == "customer.subscription.updated":
            self.handle_subscription_updated(event["data"]["object"])

        # ✅ 3. Subscription Fully Cancelled
        elif event["type"] == "customer.subscription.deleted":
            self.handle_subscription_deleted(event["data"]["object"])

        return HttpResponse(status=200)

    def get_webhook_secret(self):
        """
        Decide webhook secret based on environment
        """
        if settings.STRIPE_ENV == "live":
            return settings.STRIPE_WEBHOOK_SECRET_LIVE
        return settings.STRIPE_WEBHOOK_SECRET_TEST

    def handle_checkout_completed(self, session):
        metadata = session.get("metadata", {})
        org_id = metadata.get("org_id")
        org = Organization.objects.get(id=org_id)
        org_schema = org.schema_name 


        # ✅ Create payment transaction centrally
        from payments.services import create_payment_transaction
        print("Creating payment transaction for session:", session['id'])
        create_payment_transaction(
            org_schema=org_schema,
            organization_id=org_id,
            amount=session['amount_total'] / 100,
            currency=session['currency'],
            gateway='stripe',
            gateway_transaction_id=session['id'],
            status='success',
            metadata=metadata,
            customer_email=session.get('customer_email'),
            receipt_url=session.get('receipt_url')
        )

     
    # ================================
    # 🟡 UPGRADE / CANCEL AT PERIOD END
    # ================================
    def handle_subscription_updated(self, sub_data):

        stripe_sub_id = sub_data["id"]

        subscription = OrganizationSubscription.objects.filter(
            stripe_subscription_id=stripe_sub_id
        ).first()

        if not subscription:
            return

        # Update plan (Upgrade/Downgrade)
        stripe_price_id = sub_data["items"]["data"][0]["price"]["id"]
        new_plan = SubscriptionPlan.objects.filter(
            stripe_price_id=stripe_price_id
        ).first()

        if new_plan:
            subscription.plan = new_plan

        subscription.status = sub_data["status"]
        subscription.auto_renew = not sub_data["cancel_at_period_end"]

        subscription.start_date = timezone.datetime.fromtimestamp(
            sub_data["current_period_start"],
            tz=timezone.utc
        )

        subscription.end_date = timezone.datetime.fromtimestamp(
            sub_data["current_period_end"],
            tz=timezone.utc
        )

        subscription.save()

    # ================================
    # 🔴 FULL CANCEL
    # ================================
    def handle_subscription_deleted(self, sub_data):

        stripe_sub_id = sub_data["id"]

        subscription = OrganizationSubscription.objects.filter(
            stripe_subscription_id=stripe_sub_id
        ).first()

        if not subscription:
            return

        subscription.status = "cancelled"
        subscription.end_date = timezone.now()
        subscription.auto_renew = False
        subscription.save()

  