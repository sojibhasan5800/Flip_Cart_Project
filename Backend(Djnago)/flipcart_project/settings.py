# flipcart_project/settings/base.py
from pathlib import Path
from datetime import timedelta
import cloudinary
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Basic Config
SECRET_KEY = config('SECRET_KEY', default='django-insecure-ym8a4^z1je)5nww3s6jgf4=7md$1_nrda&-b^y+taa@!3u(otb')
DEBUG = False  # local.py, docker.py, production.py এ ওভাররাইড হবে
ALLOWED_HOSTS = []

# Installed Apps
SHARED_APPS = [
    'django_tenants',
    'daphne',
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'accounts',
    'merchant_user',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework.authtoken',
    'rest_framework_simplejwt.token_blacklist',
    'django_filters',
    'cloudinary_storage',
    'corsheaders',
    'drf_yasg',
    'channels',
    'colorfield',
    'django_celery_results',
    'django_celery_beat',
    'tenant_schemas_celery',
    # 'django_elasticsearch_dsl',
    # 'django_elasticsearch_dsl_drf',
    'admin_thumbnails',
    'public_data',
    'system_management', 
    'billing', 
    # 'core_notifications',
]

TENANT_APPS = [
    'category',
    'store',
    'carts',
    'orders',
    # 'seller_dashboard',
    'admin_core',
    # 'orders_management',
    # 'transactions',
    'payments',        # Order payment gateway
    # 'store_notifications',   # Store notifications
    # 'analytics',
]

INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]

# django-tenants Config
TENANT_MODEL = "merchant_user.Organization"
TENANT_DOMAIN_MODEL = "merchant_user.OrganizationDomain"
DATABASE_ROUTERS = ('django_tenants.routers.TenantSyncRouter',)
PUBLIC_SCHEMA_NAME = 'public'
TENANT_SUBFOLDER_PREFIX = 'tenants'
TENANT_USES_SUBDOMAINS = True
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True
BASE_ORGANIZATION_DOMAIN = config('BASE_ORGANIZATION_DOMAIN', default='localhost:8000')

# Middleware
MIDDLEWARE = [
    'django_tenants.middleware.main.TenantMainMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'flipcart_project.app_middleware.admin_core_app.tenant_admin.TenantAdminMiddleware',
    'flipcart_project.app_middleware.merchant_user_app.productApiview.MerchantProductMiddleware',
]

ROOT_URLCONF = 'flipcart_project.urls'
WSGI_APPLICATION = 'flipcart_project.wsgi.application'
ASGI_APPLICATION = 'flipcart_project.asgi.application'
AUTH_USER_MODEL = 'accounts.Account'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'DIRS': [BASE_DIR / 'templates'],
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Static & Media
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'flipcart_project/static']
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_AUTHENTICATION_CLASSES': ['rest_framework_simplejwt.authentication.JWTAuthentication'],
}

# Simple JWT
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(days=1),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
}

# Auth Validators
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Dhaka'
USE_I18N = True
USE_TZ = True

# Messages
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {messages.ERROR: 'danger'}

# Email
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'sojibhasan5800@gmail.com'
EMAIL_HOST_PASSWORD = 'oewycxrcvulmlvjr'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Stripe
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')
STRIPE_ENDPOINT_SECRET = config('STRIPE_ENDPOINT_SECRET')

# URLs
NGROK_URL = 'https://dino-staminal-kamila.ngrok-free.dev'
CSRF_TRUSTED_ORIGINS = ["http://localhost:3000", "http://10.237.106.29:3000"]
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
FRONTEND_URL = "http://localhost:3000"  # ওভাররাইড হবে

# RabbitMQ
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'
RABBITMQ_VHOST = '/'
RABBITMQ_QUEUE = 'order_queue'
RABBITMQ_EXCHANGE = 'orders_exchange'
RABBITMQ_ROUTING_KEY = 'order.created'
RABBITMQ_SELLER_QUEUE = 'seller_events'
RABBITMQ_SELLER_EXCHANGE = 'seller_exchange'
RABBITMQ_SELLER_ROUTING_KEY = 'seller.event'



# Elasticsearch
ELASTICSEARCH_OFFLINE = True
ELASTICSEARCH_DSL = {
    'default': {
        # 'hosts': 'http://localhost:9200',
        'hosts': 'http://localhost:9200',
    }
}
# ELASTICSEARCH_SIGNAL_PROCESSOR = "store.es_signal_processor.ConditionalSignalProcessor"

# SSLCommerz
SSLCZ_STORE_ID = "trans68369e6df24cb"
SSLCZ_STORE_PASS = "trans68369e6df24cb@ssl"
SSLCZ_IS_SANDBOX = True


# ImageKit
IMAGEKIT_PUBLIC_KEY = "public_K/Li/QIxreloJJo5Xc4yG8So9X8="
IMAGEKIT_PRIVATE_KEY = "private_MlLDeuFx9gF6XWrRujo8h7Mklow="
IMAGEKIT_URL_ENDPOINT = "https://ik.imagekit.io/ehdyydeuq"

# Celery Common
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Dhaka'
CELERY_ENABLE_UTC = False
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 1800
CELERY_TASK_SOFT_TIME_LIMIT = 1800
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'
# Channels setup 
# Redis common variables (default local)
REDIS_HOST = '127.0.0.1'          # docker-এ 'redis' হবে, production-এ cloud host
REDIS_PORT = 6379                 # সাধারণত 6379, TLS হলে 6380 বা অন্য
REDIS_DB = 0                      # optional, broker/result/cache-এর জন্য আলাদা db ব্যবহার করতে পারো

REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

# Cache (যদি ব্যবহার করো)
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}
# # ImageKit
IMAGEKIT_PUBLIC_KEY = "public_K/Li/QIxreloJJo5Xc4yG8So9X8="
IMAGEKIT_PRIVATE_KEY = "private_MlLDeuFx9gF6XWrRujo8h7Mklow="
IMAGEKIT_URL_ENDPOINT = "https://ik.imagekit.io/ehdyydeuq"

# # -----------------------------
# # Cloudinary (only for production)
# # -----------------------------
# # if not DEBUG:
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dwemgnaux',
    'API_KEY': '986429826285289',
    'API_SECRET': '3-_GLoBXW5SvXyCNPrbv4-QGDgg',
}

DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

cloudinary.config(
    cloud_name=CLOUDINARY_STORAGE['CLOUD_NAME'],
    api_key=CLOUDINARY_STORAGE['API_KEY'],
    api_secret=CLOUDINARY_STORAGE['API_SECRET']
)

# bKash config (add to your settings)
BKASH_BASE_URL = 'https://checkout.sandbox.bka.sh/v1.2.0-beta'  # Sandbox, production-এ চেঞ্জ করুন
BKASH_APP_KEY = config('BKASH_APP_KEY')
BKASH_APP_SECRET = config('BKASH_APP_SECRET')
BKASH_USERNAME = config('BKASH_USERNAME')
BKASH_PASSWORD = config('BKASH_PASSWORD')
BKASH_SUCCESS_CALLBACK = 'https://your-domain.com/api/payments/bkash/success/'  # Your frontend or backend URL
BKASH_FAIL_CALLBACK = 'https://your-domain.com/api/payments/bkash/fail/'
BKASH_CANCEL_CALLBACK = 'https://your-domain.com/api/payments/bkash/cancel/'

#