from django_celery_beat.models import PeriodicTask, CrontabSchedule
import json
from django.utils import timezone
from decimal import Decimal

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


def calculate_proration(current_subscription, new_plan):
    """
    Returns a dict with proration info:
    - remaining_days: unused days in current period
    - amount_due: positive (upgrade) or negative (credit) in Decimal
    - new_end_date: period end for new plan
    """
    now = timezone.now()
    current_plan = current_subscription.plan
    if not current_subscription.end_date:
        # Treat as full cycle
        remaining_days = current_plan.get_duration()
    else:
        remaining_days = (current_subscription.end_date - now).days
        remaining_days = max(remaining_days, 0)

    # Daily rates
    current_daily = Decimal(current_plan.price) / Decimal(current_plan.get_duration())
    new_daily = Decimal(new_plan.price) / Decimal(new_plan.get_duration())

    # Credit/charge
    credit = current_daily * Decimal(remaining_days)
    charge = new_daily * Decimal(remaining_days)
    amount_due = charge - credit

    new_end_date = now + timezone.timedelta(days=new_plan.get_duration())

    return {
        "remaining_days": remaining_days,
        "current_daily": current_daily,
        "new_daily": new_daily,
        "credit": round(credit, 2),
        "charge": round(charge, 2),
        "amount_due": round(amount_due, 2),
        "new_end_date": new_end_date
    }












