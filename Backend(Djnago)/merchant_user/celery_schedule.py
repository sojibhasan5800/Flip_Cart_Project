from celery.schedules import crontab

SELLER_DASHBOARD_BEAT_SCHEDULE = {
    'update-active-merchant-dashboards-every-minute': {
        'task': 'merchant_user.tasks.update_active_merchant_dashboards',
        'schedule': crontab(minute='*/1'),
        'options': {
            'queue': 'periodic'
        }
    },
}
