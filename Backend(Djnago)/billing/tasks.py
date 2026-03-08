from turtle import down

from celery import shared_task
from django.utils import timezone
from .models import OrganizationSubscription


@shared_task
def expire_subscription_task(subscription_id):
    """
    Task runs 5 minutes before subscription end
    """
    try:
        sub = OrganizationSubscription.objects.get(id=subscription_id)
        org = sub.organization
        now = timezone.now()
        if sub.status != 'active':
            return

        # Expire subscription if end_date passed
        if sub.end_date <= now:
            if sub.pending_plan and sub.change_type == "downgrade":
                # Apply scheduled downgrade
                sub.plan = sub.pending_plan
                sub.pending_plan = None
                sub.change_type = None
                sub.scheduled_change_at = None
                sub.end_date = now + timezone.timedelta(days=sub.plan.get_duration())
                sub.save(update_fields=['plan', 'pending_plan', 'change_type', 'scheduled_change_at', 'end_date'])
                org.subscription_plan_level = sub.plan.plan_level
                org.subscription_current_period_start = now
                org.subscription_current_period_end = sub.end_date
                org.save(update_fields=['subscription_plan_level', 'subscription_current_period_start', 'subscription_current_period_end'])
                send_expire_sms(sub.organization.id,downgrade=True)
            else:
                sub.status = 'expired'
                sub.is_expiring_soon = False
                sub.save(update_fields=['status', 'is_expiring_soon'])
                org.subscription_status = 'expired'
                org.save(update_fields=['subscription_status'])

                send_expire_sms(sub.organization.id)
        else:
            # If subscription extended, reschedule task
            sub.save()
    except OrganizationSubscription.DoesNotExist:
        pass


def send_expire_sms(organization_id, downgrade=False):
    """
    Placeholder SMS logic (integrate your SMS provider)
    """
    if downgrade:
        print(f"SMS: Subscription downgraded for Organization {organization_id}")
    else:
        print(f"SMS: Subscription about to expire for Organization {organization_id}")









