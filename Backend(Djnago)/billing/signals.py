from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import OrganizationSubscription
from .tasks import schedule_expire_sms_task, remove_existing_task
from django.utils import timezone

@receiver(post_save, sender=OrganizationSubscription)
def handle_subscription_save(sender, instance: OrganizationSubscription, created, **kwargs):
    """
    Signal for:
    1️⃣ New subscription -> schedule 5-minutes-before expire task
    2️⃣ Update subscription -> remove old task & schedule new one
    """
    now = timezone.now()
    
    # Only if subscription is active and has end_date in future
    if instance.status == 'active' and instance.end_date and instance.end_date > now:
        # Mark is_expiring_soon dynamically
        instance.is_expiring_soon = instance.end_date <= (now + timezone.timedelta(minutes=5))
        instance.save(update_fields=['is_expiring_soon'])

        # Remove previous task if exists
        remove_existing_task(subscription_id=instance.id)

        # Schedule new 5-minutes-before expire task
        schedule_expire_sms_task(subscription=instance)