from global_payments.models import Invoice
from django.utils import timezone

def create_proration_invoice(subscription, proration_data, description=None):
    """
    Creates an invoice object for proration charges
    """
    if not description:
        description = f"Proration for upgrade to {subscription.plan.name}"

    invoice = Invoice.objects.create(
        organization=subscription.organization,
        subscription=subscription,
        amount=proration_data["amount_due"],
        currency=subscription.plan.currency,
        status="pending",
        issued_at=timezone.now(),
        due_at=timezone.now() + timezone.timedelta(days=14),
        line_items=[
            {
                "description": description,
                "amount": float(proration_data["amount_due"]),
                "credit": float(proration_data["credit"]),
                "charge": float(proration_data["charge"]),
                "days_remaining": proration_data["remaining_days"]
            }
        ]
    )
    return invoice