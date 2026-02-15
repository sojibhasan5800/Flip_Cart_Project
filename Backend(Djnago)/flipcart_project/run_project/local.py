# flipcart_project/run_project/local.py
from flipcart_project.settings import *   # ← সঠিক import (তোমার স্ট্রাকচার অনুযায়ী)

# Local development overrides
DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': 'GocartDB',
        'USER': 'postgres',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

# Redis / Channels / Cache / Celery overrides for local
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}'

# base-এ define করা CHANNEL_LAYERS ও CACHES আপডেট
CHANNEL_LAYERS['default']['CONFIG']['hosts'] = [(REDIS_HOST, REDIS_PORT)]
CACHES['default']['LOCATION'] = f"{REDIS_URL}/1"

CELERY_BROKER_URL = f'{REDIS_URL}/0'
CELERY_RESULT_BACKEND = f'{REDIS_URL}/1'

BASE_URL = "http://127.0.0.1:8000"
FRONTEND_URL = "http://localhost:3000"