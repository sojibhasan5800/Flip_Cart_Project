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
    permission_classes = [AllowAny]  # Stripe is not authenticated

    def post(self, request, *args, **kwargs):
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE")

        try:
            event = stripe.Webhook.construct_event(
                payload=payload,
                sig_header=sig_header,
                secret=settings.STRIPE_WEBHOOK_SECRET
            )
        except stripe.error.SignatureVerificationError:
            return HttpResponse(status=400)
        except ValueError:
            return HttpResponse(status=400)

        # ✅ Handle event
        if event["type"] == "checkout.session.completed":
            self.handle_checkout_completed(event["data"]["object"])

        return HttpResponse(status=200)

    def handle_checkout_completed(self, session):
        """
        This method is separated for clean architecture
        """
        metadata = session.get("metadata", {})
        plan_id = metadata.get("plan_id")
        user_id = metadata.get("user_id")
        tenant_id = metadata.get("tenant_id")

        if not plan_id or not user_id:
            return

        # ✅ Activate subscription safely
        # activate_subscription(
        #     user_id=user_id,
        #     plan_id=plan_id,
        #     tenant_id=tenant_id,
        #     stripe_session_id=session.get("id"),
        #     amount=session.get("amount_total"),
        #     currency=session.get("currency"),
        # )