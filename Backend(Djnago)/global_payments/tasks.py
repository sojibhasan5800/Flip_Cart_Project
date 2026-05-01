from celery import shared_task
from .models import SubscriptionPaymentTransaction

@shared_task
def verify_payment(trans_id):
    trans = SubscriptionPaymentTransaction.objects.get(id=trans_id)
    # Extra verification logic if needed (e.g., poll bKash)
    trans.verify_and_complete()