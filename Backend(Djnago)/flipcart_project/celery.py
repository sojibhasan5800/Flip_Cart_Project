import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flipcart_project.settings')
app = Celery('flipcart_project')

# RabbitMQ Broker + Redis Backend
app.conf.broker_url = 'amqp://guest:guest@localhost:5672//'
app.conf.result_backend = 'redis://127.0.0.1:6379/0'

app.config_from_object('django.conf:settings', namespace='CELERY')

# Set timezone
app.conf.enable_utc = False
app.conf.timezone = 'Asia/Dhaka'
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'update-seller-analytics-hourly': {
        'task': 'seller_dashboard.tasks.update_all_seller_analytics',
        'schedule': crontab(minute='*/5'),  # ever five minutes after 1 time task work
    },
}

# ---------------------CUPON EXPIRY TASKS---------------------

# celery.py (in your project root)
import os
from celery import Celery
from celery.schedules import crontab
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flipcart_project.settings')

app = Celery('flipcart_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    # Backup task: Check for missed expiries every 6 hours
    'bulk-expire-check-every-6-hours': {
        'task': 'coupon.tasks.bulk_expire_coupons_check',
        'schedule': crontab(hour='*/6'),  # Every 6 hours
        'options': {'expires': 3600}  # 1 hour
    },
    # Cleanup old coupons weekly
    'cleanup-old-coupons-weekly': {
        'task': 'coupon.tasks.cleanup_old_coupons',
        'schedule': crontab(day_of_week='sunday', hour=3),  # Sunday 3 AM
        'options': {'expires': 3600}
    },
    # Health check for Celery tasks
    'coupon-health-check': {
        'task': 'coupon.tasks.health_check',
        'schedule': crontab(minute='*/30'),  # Every 30 minutes
    },
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')


# -------------- END CUPON EXIPIRCY TASK ----------------------

