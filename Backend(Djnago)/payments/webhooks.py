# billing/webhooks.py
import stripe
from django.conf import settings
from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

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
            self.handle_checkout_completed(event["data"]["object"])

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
        plan_id = metadata.get("plan_id")
        user_id = metadata.get("user_id")
        tenant_id = metadata.get("tenant_id")

        if not plan_id or not user_id:
            return

        # ✅ Production safe activation (example)
        # activate_subscription(
        #     user_id=user_id,
        #     plan_id=plan_id,
        #     tenant_id=tenant_id,
        #     stripe_session_id=session["id"],
        #     amount=session["amount_total"],
        #     currency=session["currency"],
        # )