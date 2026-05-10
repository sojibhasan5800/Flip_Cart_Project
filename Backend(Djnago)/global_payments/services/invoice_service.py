
import uuid

from global_payments.models import Invoice


def generate_invoice(payment_transaction):

    invoice = Invoice.objects.create(
        transaction=payment_transaction,
        invoice_number=f"INV-{uuid.uuid4().hex[:12]}",
        payment_type=payment_transaction.payment_for,
        amount=payment_transaction.amount,
        status="paid",
        line_items=[
            {
                "title": payment_transaction.payment_for,
                "amount": str(payment_transaction.amount)
            }
        ]
    )

    return invoice