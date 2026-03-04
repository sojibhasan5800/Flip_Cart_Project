from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json
from django.utils import timezone

def schedule_expire_sms_task(subscription):
    """
    Schedule a 5-minute-before expire Celery beat task for a specific subscription/schema
    """
    task_name = f"expire-sub-{subscription.id}-schema-{subscription.organization.schema_name}"

    # Remove existing task first
    # PeriodicTask.objects.filter(name=task_name).delete()

    expire_time = subscription.end_date - timezone.timedelta(minutes=5)

    schedule, _ = CrontabSchedule.objects.get_or_create(
        minute=str(expire_time.minute),
        hour=str(expire_time.hour),
        day_of_month=str(expire_time.day),
        month_of_year=str(expire_time.month),
        timezone='UTC'
    )

    PeriodicTask.objects.create(
        crontab=schedule,
        name=task_name,
        task='billing.tasks.expire_subscription_task',
        args=json.dumps([subscription.id]),
        one_off=True,  # run only once
    )

def remove_existing_task(subscription_id):
    """
    Remove any previously scheduled task for this subscription
    """
    PeriodicTask.objects.filter(name__startswith=f"expire-sub-{subscription_id}-").delete()

















