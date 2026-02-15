# seller_dashboard/management/commands/setup_dashboard_scheduler.py
from django.core.management.base import BaseCommand
from django_celery_beat.models import PeriodicTask, IntervalSchedule
from django.utils import timezone

class Command(BaseCommand):
    help = 'Setup or reset the active merchant dashboard update schedule'

    def handle(self, *args, **options):
        # পুরনো টাস্ক মুছে ফেলা (যদি থাকে)
        PeriodicTask.objects.filter(name='update-active-merchant-dashboards-every-minute').delete()

        # Interval তৈরি (প্রতি ১ মিনিট)
        schedule, created = IntervalSchedule.objects.get_or_create(
            every=1,
            period=IntervalSchedule.MINUTES,
        )

        # নতুন PeriodicTask তৈরি
        task = PeriodicTask.objects.create(
            interval=schedule,
            name='update-active-merchant-dashboards-every-minute',
            task='merchant_user.tasks.update_active_merchant_dashboards',  # ← তোমার task path
            enabled=True,  # ডিফল্ট চালু
            queue='periodic',  # optional — তোমার queue
            description='Updates dashboard stats for currently active merchants every 1 minute',
        )

        self.stdout.write(self.style.SUCCESS(
            f'Successfully created/updated schedule: {task.name}\n'
            f'Enabled: {task.enabled}\n'
            f'Interval: every {schedule.every} {schedule.period}'
        ))