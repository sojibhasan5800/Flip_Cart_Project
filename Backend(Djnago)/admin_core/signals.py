from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Coupon

@receiver(post_save, sender=Coupon)
def manage_coupon_expiry_task(sender, instance, created, **kwargs):
    if created:
        if instance.is_active and instance.valid_to > timezone.now():
            instance.schedule_expiry_task()
    else:
        # update হলে reschedule
        if instance.celery_task_id and instance.valid_to > timezone.now():
            instance.cancel_scheduled_task()
            instance.schedule_expiry_task()

