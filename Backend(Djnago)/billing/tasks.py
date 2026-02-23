

# billing/tasks.py (Extended from previous, added lifecycle, invoice gen)
from celery import shared_task
from django_redis import get_redis_connection
from django.utils import timezone
from .models import OrganizationSubscription, SubscriptionPlan, Invoice
from store.models import Product
from django_tenants.utils import schema_context
import json
import stripe
from django.conf import settings
from reportlab.lib.pagesizes import letter  # For PDF gen, install reportlab if needed
from reportlab.pdfgen import canvas
import os
from cloudinary.uploader import upload  # Assuming Cloudinary for PDF storage

@shared_task(bind=True, max_retries=3)
def sync_boosted_product_to_redis(self, product_id: int, schema_name: str):
    # Same as previous, no change
    pass  # Implement as before

@shared_task
def check_expired_boosts():
    # Same as previous
    pass  # Implement as before

@shared_task
def update_stripe_subscription(sub_id: int):
    sub = OrganizationSubscription.objects.get(id=sub_id)
    try:
        stripe.Subscription.modify(
            sub.stripe_subscription_id,
            items=[{'price': sub.plan.stripe_price_id}],
        )
    except stripe.error.StripeError as e:
        # Log error
        pass

@shared_task
def schedule_downgrade(sub_id: int, new_plan_id: int):
    # Use Celery beat or delay till end_date
    sub = OrganizationSubscription.objects.get(id=sub_id)
    new_plan = SubscriptionPlan.objects.get(id=new_plan_id)
    # Wait till end_date, then update
    delay_seconds = (sub.end_date - timezone.now()).total_seconds()
    apply_downgrade.apply_async((sub_id, new_plan_id), countdown=delay_seconds)

@shared_task
def apply_downgrade(sub_id: int, new_plan_id: int):
    sub = OrganizationSubscription.objects.get(id=sub_id)
    new_plan = SubscriptionPlan.objects.get(id=new_plan_id)
    sub.plan = new_plan
    sub.start_date = timezone.now()
    sub.end_date = sub.start_date + timezone.timedelta(days=new_plan.get_duration())
    sub.save()
    update_stripe_subscription.delay(sub.id)

@shared_task
def generate_invoice_pdf(invoice_id: int):
    invoice = Invoice.objects.get(id=invoice_id)
    file_path = f"/tmp/invoice_{invoice.invoice_number}.pdf"
    c = canvas.Canvas(file_path, pagesize=letter)
    # Draw PDF content (simple example)
    c.drawString(100, 750, f"Invoice {invoice.invoice_number}")
    c.drawString(100, 730, f"Amount: {invoice.amount} {invoice.currency}")
    c.drawString(100, 710, f"Organization: {invoice.organization.business_name}")
    # Add line items
    y = 690
    for item in invoice.line_items:
        c.drawString(100, y, f"{item['description']}: {item['amount']}")
        y -= 20
    c.save()
    
    # Upload to Cloudinary
    upload_result = upload(file_path, resource_type="raw")
    invoice.pdf_url = upload_result['secure_url']
    invoice.save()
    os.remove(file_path)

@shared_task
def handle_stripe_event(event_data: dict):
    """Stripe lifecycle handler (called from webhook)"""
    event = stripe.Event.construct_from(event_data, stripe.api_key)
    if event.type == 'invoice.paid':
        invoice = Invoice.objects.get(stripe_invoice_id=event.data.object.id)
        invoice.status = 'paid'
        invoice.paid_at = timezone.now()
        invoice.save()
    elif event.type == 'invoice.payment_failed':
        invoice = Invoice.objects.get(stripe_invoice_id=event.data.object.id)
        invoice.status = 'failed'
        invoice.save()
        # Notify merchant
    elif event.type == 'customer.subscription.deleted':
        sub = OrganizationSubscription.objects.get(stripe_subscription_id=event.data.object.id)
        sub.status = 'cancelled'
        sub.auto_renew = False
        sub.save()
    # Add more events as needed for lifecycle 


