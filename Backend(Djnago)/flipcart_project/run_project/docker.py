# flipcartproject/settings/docker.py
from flipcart_project.settings import *

DEBUG = True
ALLOWED_HOSTS = ['*']

DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': config('POSTGRES_DB', default='flipcart_db'),
        'USER': config('POSTGRES_USER', default='flipcart_user'),
        'PASSWORD': config('POSTGRES_PASSWORD', default='flipcart_pass'),
        'HOST': 'db',
        'PORT': '5432',
    }
}

REDIS_HOST = 'redis'
REDIS_PORT = 6379
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}'

CHANNEL_LAYERS['default']['CONFIG']['hosts'] = [(REDIS_HOST, REDIS_PORT)]
CACHES['default']['LOCATION'] = f"{REDIS_URL}/1"

CELERY_BROKER_URL = f'{REDIS_URL}/0'
CELERY_RESULT_BACKEND = f'{REDIS_URL}/1'


ELASTICSEARCH_OFFLINE = False

ELASTICSEARCH_DSL = {
    'default': {
        'hosts': ['http://elasticsearch:9200'],  # docker-compose service name
        'timeout': 30,
        'retry_on_timeout': True,
        'verify_certs': False,
    }
}