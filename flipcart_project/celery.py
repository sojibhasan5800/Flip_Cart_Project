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
