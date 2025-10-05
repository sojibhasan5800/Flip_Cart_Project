"""
Django settings for flipcart_project project.
Clean version for Localhost + Production
"""

from pathlib import Path
import dj_database_url
import cloudinary
from decouple import config

# BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------
# Basic Config
# -----------------------------
SECRET_KEY = 'django-insecure-ym8a4^z1je)5nww3s6jgf4=7md$1_nrda&-b^y+taa@!3u(otb'

# Localhost এ কাজ করার জন্য True রাখুন, deploy করলে False দিন
DEBUG = True

ALLOWED_HOSTS = (
    ['*'] if DEBUG else ['flip-cart-project-1.onrender.com']
)


# -----------------------------
# Installed Apps
# -----------------------------
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third-party
    'rest_framework',
    'rest_framework.authtoken',
    'django_filters',
    'cloudinary_storage',
    'drf_yasg',
    'admin_thumbnails',

    # Local apps
    'accounts',
    'category',
    'store',
    'carts',
    'orders',
    'seller_dashboard',
]

# -----------------------------
# Middleware
# -----------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Custom Middleware
    'flipcart_project.middleware.user_activity.UserActivityMiddleware',
    'flipcart_project.middleware.performance.PerformanceMiddleware',
    'flipcart_project.middleware.security.SecurityMiddleware',
]

ROOT_URLCONF = 'flipcart_project.urls'
WSGI_APPLICATION = 'flipcart_project.wsgi.application'
AUTH_USER_MODEL = 'accounts.Account'

# -----------------------------
# Templates
# -----------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'category.context_processors.menu_links',
                'carts.context_processors.counter',
            ],
        },
    },
]

# -----------------------------
# Database
# -----------------------------
if DEBUG:
    # Localhost: SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Production: Postgres (Render)
    DATABASES = {
        'default': dj_database_url.config(
            default='postgresql://flip_data_user:hINuFmo29D1wMLpsFhEsTdTYQBSJiFbg@dpg-d2r8cqmr433s73fa64n0-a.oregon-postgres.render.com/flip_data'
        )
    }

# -----------------------------
# Static & Media Files
# -----------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'flipcart_project/static']
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# -----------------------------
# Cloudinary (only for production)
# -----------------------------
# if not DEBUG:
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

# -----------------------------
# REST Framework
# -----------------------------
REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}

# -----------------------------
# Security Settings
# -----------------------------
if not DEBUG:
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

# -----------------------------
# Auth Validators
# -----------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -----------------------------
# Internationalization
# -----------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# -----------------------------
# Messages
# -----------------------------
from django.contrib.messages import constants as messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# -----------------------------
# Email Config
# -----------------------------
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'sojibhasan5800@gmail.com'
EMAIL_HOST_PASSWORD = 'oewycxrcvulmlvjr'  

# -----------------------------
# Default Primary Key
# -----------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'



# -----------------------------
#  Stripe Keys Config
# -----------------------------
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY')
STRIPE_ENDPOINT_SECRET = config('STRIPE_ENDPOINT_SECRET')


# -----------------------------
#  Base_url Config
# -----------------------------
NGROK_URL = 'https://dino-staminal-kamila.ngrok-free.dev'
CSRF_TRUSTED_ORIGINS = ['https://dino-staminal-kamila.ngrok-free.dev']

if NGROK_URL:
    BASE_URL = NGROK_URL
    
else:
    if DEBUG:
        BASE_URL = "http://127.0.0.1:8000/"
    else:
        BASE_URL= "https://flip-cart-project-1.onrender.com"
# CSRF_TRUSTED_ORIGINS.append(BASE_URL)

# -----------------------------
# Channels setup
# -----------------------------
ASGI_APPLICATION = 'flipcart_project.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}


# -----------------------------
# Celery config
# -----------------------------
CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
CELERY_RESULT_BACKEND = 'redis://127.0.0.1:6379/0'


# -----------------------------
#  RabbitMQ Config
# -----------------------------

# Point: RabbitMQ Configuration (Direct Variables)
RABBITMQ_HOST = 'localhost'
RABBITMQ_PORT = 5672
RABBITMQ_USER = 'guest'
RABBITMQ_PASSWORD = 'guest'
RABBITMQ_VHOST = '/'
RABBITMQ_QUEUE = 'order_queue'
RABBITMQ_EXCHANGE = 'orders_exchange'
RABBITMQ_ROUTING_KEY = 'order.created'
