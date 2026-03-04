# billing/webhooks.py
from operator import sub

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
        stripe_subscription_id = session.get("subscription")
        print("stripe_subscription_id",stripe_subscription_id)

        if not stripe_subscription_id:
            return
        sub = stripe.Subscription.retrieve(stripe_subscription_id)

        subscription_item_id = sub["items"]["data"][0]["id"]
        stripe_price_id = sub["items"]["data"][0]["price"]["id"]
    
        if subscription_item_id:
            metadata["stripe_subscription_item_id"] = subscription_item_id
            metadata["stripe_price_id"] = stripe_price_id
            metadata["stripe_subscription_id"] = stripe_subscription_id


        # ✅ Create payment transaction centrally
        from payments.services import create_payment_transaction

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
        stripe_sub_id = sub_data.get("id")
        subscription = OrganizationSubscription.objects.filter(stripe_subscription_id=stripe_sub_id).first()
        if not subscription:
            return

        # Sync plan if changed (upgrade)
        stripe_items = sub_data.get("items", {}).get("data", [])
        if stripe_items:
            stripe_price_id = stripe_items[0].get("price", {}).get("id")
            new_plan = SubscriptionPlan.objects.filter(stripe_price_id=stripe_price_id).first()
            if new_plan and new_plan != subscription.plan:
                subscription.plan = new_plan

        # Sync status
        cancel_at_period_end = sub_data.get("cancel_at_period_end", False)
        stripe_status = sub_data.get("status", "active")
        subscription.status = "cancel_pending" if cancel_at_period_end else stripe_status
        subscription.auto_renew = not cancel_at_period_end

        # Sync period dates
        subscription.start_date = timezone.datetime.fromtimestamp(
            sub_data.get("current_period_start", timezone.now().timestamp()), tz=timezone.utc
        )
        subscription.end_date = timezone.datetime.fromtimestamp(
            sub_data.get("current_period_end", timezone.now().timestamp()), tz=timezone.utc
        )

        # Handle scheduled downgrade
        if getattr(subscription, "downgrade_at_period_end", False):
            now = timezone.now()
            if subscription.end_date <= now:
                new_plan = SubscriptionPlan.objects.filter(id=subscription.downgrade_plan_id).first()
                if new_plan:
                    subscription.plan = new_plan
                    subscription.downgrade_at_period_end = False
                    subscription.downgrade_plan_id = None
                    # Update Stripe subscription at period end
                    try:
                        stripe.Subscription.modify(
                            stripe_sub_id,
                            items=[{
                                "id": subscription.stripe_subscription_item_id,
                                "price": new_plan.stripe_price_id
                            }],
                            proration_behavior="none"
                        )
                    except stripe.error.StripeError as e:
                        print("Stripe downgrade error:", e)

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

  