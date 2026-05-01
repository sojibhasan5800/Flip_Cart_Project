import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(user, plan):
    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        line_items=[{
            "price": plan.stripe_price_id,
            "quantity": 1,
        }],
        success_url=f"{settings.FRONTEND_URL}/success?session_id={{CHECKOUT_SESSION_ID}}",
        cancel_url=f"{settings.FRONTEND_URL}/cancel",
        metadata={
            "type": "customer_subscription",
            "user_id": str(user.id),
            "plan_id": str(plan.id),
        },
        client_reference_id=str(user.id),
    )

    return session