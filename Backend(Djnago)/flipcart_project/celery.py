# flipcart_project/celery.py
import os
from celery import Celery

# Django settings লোড করা
os.environ.setdefault(
    'DJANGO_SETTINGS_MODULE',
    'flipcart_project.run_project.local'
)

app = Celery('flipcart_project')

# ========================
# BROKER & BACKEND
# ========================
app.conf.broker_url = 'amqp://guest:guest@localhost:5672//'
app.conf.result_backend = 'redis://127.0.0.1:6379/0'

# ========================
# DJANGO SETTINGS LOAD
# ========================
app.config_from_object('django.conf:settings', namespace='CELERY')

# ========================
# TIMEZONE
# ========================
app.conf.enable_utc = False
app.conf.timezone = 'Asia/Dhaka'

# ========================
# TASK DISCOVERY
# ========================
app.autodiscover_tasks()

# ========================
# BEAT SCHEDULE — এখানে তোমার schedule সেট করা হচ্ছে
# ========================
# from merchant_user.celery_schedule import SELLER_DASHBOARD_BEAT_SCHEDULE

# app.conf.beat_schedule = SELLER_DASHBOARD_BEAT_SCHEDULE

# ========================
# Optional: Debug-এর জন্য print করতে পারো (চাইলে রাখো)
# ========================
print("Celery Beat Schedule loaded:")