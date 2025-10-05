import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'flipcart_project.settings')
app = Celery('flipcart_project')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'update-seller-analytics-hourly': {
        'task': 'seller_dashboard.tasks.update_all_seller_analytics',
        'schedule': crontab(minute='*/5'),  # ever five minutes after 1 time task work
    },
}
