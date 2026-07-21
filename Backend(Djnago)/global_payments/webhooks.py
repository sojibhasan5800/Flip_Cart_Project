# billing/webhooks.py
from operator import sub

from asgiref.sync import async_to_sync
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from channels.layers import get_channel_layer
from django.utils import timezone
from django.db import transaction
import stripe
from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from datetime import  timedelta

from billing.models import OrganizationSubscription, SubscriptionPlan
from merchant_user.models import Organization

from global_payments.services.subscription_service import activate_organization_subscription,activate_product_boost_subscription,activate_customer_subscription
from global_payments.services.transaction_service import create_payment_transaction
from .tasks import process_successful_payment
from analytics_engine.tasks.payment_tasks import create_payment_analytics

stripe.api_key = settings.STRIPE_SECRET_KEY


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    permission_classes = [AllowAny]
    

    def post(self, request, *args, **kwargs):
        
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        #  Select correct webhook secret
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
                print(f"[Webhook DEBUG] Checkout session completed event received: {event['data']['object']}")
                self.handle_checkout_completed(event["data"]["object"])
            except Exception as e:
                print("Webhook processing failed:", str(e))
                return HttpResponse("Processing error", status=500)
                # ✅ 2. Subscription Updated (Upgrade / Cancel at period end)
        elif event["type"] == "customer.subscription.updated":
            print(f"[Webhook DEBUG] Subscription updated event received: {event['data']['object']}")
            self.handle_subscription_updated(event["data"]["object"])

        # ✅ 3. Subscription Fully Cancelled
        elif event["type"] == "customer.subscription.deleted":
            print(f"[Webhook DEBUG] Subscription deleted event received: {event['data']['object']}")
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
        print(f"[Webhook DEBUG] Checkout session completed with metadata: {metadata}")

        plan_type = metadata.get("plan_type")
 
        stripe_subscription_id = session.get("subscription")
        
        if not stripe_subscription_id:
            return
        
        # ==========================================
        # Retrieve Stripe Subscription
        # ==========================================
        
        sub = stripe.Subscription.retrieve(stripe_subscription_id)
        

        subscription_item_id = sub["items"]["data"][0]["id"]
        stripe_price_id = sub["items"]["data"][0]["price"]["id"]
    
        if subscription_item_id:
            metadata["stripe_subscription_item_id"] = subscription_item_id
            metadata["stripe_price_id"] = stripe_price_id
            metadata["stripe_subscription_id"] = stripe_subscription_id
            print(f"[Webhook DEBUG] Retrieved subscription item ID: {subscription_item_id}, price ID: {stripe_price_id}, subscription ID: {stripe_subscription_id}")


        
        # ==========================================
        # PAYMENT TYPE
        # ==========================================
        
        payment_for = None

        if plan_type == "organization":

            payment_for = "organization_subscription"

        elif plan_type == "product_boost":

            payment_for = "product_boost"

        elif plan_type == "plus_membership":

            payment_for = "customer_subscription"

        else:
            return
        
        # ==========================================
        # CREATE PAYMENT TRANSACTION
        # ==========================================
        with transaction.atomic():

            transaction_obj = create_payment_transaction(

                payment_for=payment_for,

                amount=session['amount_total'] / 100,

                currency=session['currency'].upper(),

                gateway='stripe',

                gateway_transaction_id=session['id'],

                status='success',

                metadata=metadata,

                customer_email=session.get(
                    'customer_email'
                ),
            )
        
        # ==========================================
        # CREATE USER WAYS SUBSCRIPTION OBJECT
        # ==========================================
        
            if plan_type == "organization":

                activate_organization_subscription(
                    transaction_obj,
                    metadata
                )

            elif plan_type == "product_boost":

                activate_product_boost_subscription(
                    transaction_obj,
                    metadata
                )

            elif plan_type == "plus_membership":

                activate_customer_subscription(
                    transaction_obj,
                    metadata
                )

            else:
                return
        
        

        # ==========================================
        # ASYNC BACKGROUND PROCESSING
        # ==========================================
            transaction.on_commit(
                lambda: process_successful_payment.delay(
                    transaction_obj.id
                )
            )

            transaction.on_commit(
                lambda: create_payment_analytics.delay(
                    transaction_obj.id
                )
            )
    
        
     
    # ================================
    # 🟡 UPGRADE / CANCEL AT PERIOD END
    # ================================

    def handle_subscription_updated(self, sub_data):
        try:
            with transaction.atomic():
                stripe_sub_id = sub_data.get("id")
                subscription = OrganizationSubscription.objects.filter(
                    stripe_subscription_id=stripe_sub_id
                ).first()
                # print(f"Handling subscription update for Stripe Subscription ID: {stripe_sub_id}, found local subscription: {subscription is not None}")
                if not subscription:
                    return

                metadata = sub_data.get("metadata", {})
                change_type = metadata.get("change_type")
                new_plan_id = metadata.get("new_plan_id")
                # print(f"Webhook received for subscription update. Change type: {change_type}, New plan ID: {new_plan_id}")
                org_id = metadata.get("organization_id")

                stripe_items = sub_data.get("items", {}).get("data", [])
                new_plan = None
                if new_plan_id:
                    new_plan = SubscriptionPlan.objects.filter(id=new_plan_id).first()
                    # print(f"Webhook detected change_type: {change_type} for Organization ID: {org_id}, new plan ID: {new_plan_id}")
                elif stripe_items:
                    stripe_price_id = stripe_items[0].get("price", {}).get("id")
                    new_plan = SubscriptionPlan.objects.filter(stripe_price_id=stripe_price_id).first()

                # Sync status and period
                # subscription.start_date = datetime.fromtimestamp(sub_data.get("current_period_start", timezone.now().timestamp()), tz=timezone.utc)
                # subscription.end_date = datetime.fromtimestamp(sub_data.get("current_period_end", timezone.now().timestamp()), tz=timezone.utc)
                subscription.start_date = timezone.now()
                if subscription.plan:        
                    subscription.end_date = subscription.start_date + timedelta(days=subscription.plan.get_duration())

                cancel_at_period_end = sub_data.get("cancel_at_period_end", False)
                subscription.status = "cancelled" if cancel_at_period_end else sub_data.get("status", "active")
                subscription.auto_renew = not cancel_at_period_end

                # Apply upgrade or scheduled downgrade
                if new_plan and new_plan != subscription.plan:
                    if change_type == "upgrade":
                        # print(f"Webhook detected UPGRADE for {subscription.organization.business_name}")
                        subscription.plan = new_plan
                    elif change_type == "downgrade":
                        # print(f"Webhook detected DOWNGRADE for {subscription.organization.business_name}")
                        # Apply downgrade only if period ended
                        now = timezone.now()
                        if subscription.end_date <= now:
                            subscription.plan = new_plan
                        else:
                            subscription.pending_plan = new_plan
                            subscription.change_type = "downgrade"
                            subscription.scheduled_change_at = subscription.end_date

                subscription.save()
                organization = Organization.objects.filter(id=org_id).first()
                if organization:
                    organization.subscription_plan_level = subscription.plan.plan_level
                    organization.subscription_status = subscription.status
                    organization.subscription_current_period_start = subscription.start_date
                    organization.subscription_current_period_end = subscription.end_date
                    organization.is_trial = False
                    organization.save(update_fields=[
                        "subscription_plan_level",
                        "subscription_status",
                        "subscription_current_period_start",
                        "subscription_current_period_end",
                        "is_trial"
                    ])
                
                if change_type == "downgrade":
                    data ={
                        "change_type": "downgrade",
                        "status": "scheduled",
                        "current_plan": subscription.plan.name if subscription.plan else "Unknown",
                        "next_plan": new_plan.name if new_plan else "Unknown",
                        "effective_date": subscription.end_date.isoformat() if subscription.end_date else "Unknown"
                        }
                elif change_type == "upgrade":
                    data ={
                        "change_type": "upgrade",
                        "status": "effective immediately",
                        "current_plan": subscription.plan.name if subscription.plan else "Unknown",
                        "next_plan": new_plan.name if new_plan else "Unknown",
                        "effective_date": subscription.end_date.isoformat() if subscription.end_date else "Unknown"
                        }
                # ======================
                # 🔵 WebSocket push
                # ======================
                if org_id:
                    print(f"[Webhook DEBUG] Sending WS data")
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"subscription_{org_id}",
                        {
                            "type": "subscription_update",
                            "data": data
                        }
                    )
                    print(f"[Webhook DEBUG] WS data sent: {data}")
                

        except Exception as e:
            print("Webhook transaction rolled back:", str(e))
            # print(f"Organization {organization.business_name} subscription status updated to: {subscription.status}, plan level: {subscription.plan.plan_level}, period: {subscription.start_date} to {subscription.end_date}")
            # print("Organization subscription status updated to:", subscription.status) 

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

  