"""
Django settings for flipcart_project project.
Clean version for Localhost + Production
"""

from pathlib import Path
import dj_database_url
import cloudinary
from datetime import timedelta
from decouple import config

# BASE_DIR
BASE_DIR = Path(__file__).resolve().parent.parent

# -----------------------------
# Basic Config
# -----------------------------
SECRET_KEY = 'django-insecure-ym8a4^z1je)5nww3s6jgf4=7md$1_nrda&-b^y+taa@!3u(otb'

# Localhost এ কাজ করার জন্য True রাখুন, deploy করলে False দিন
DEBUG = True
USE_DOCKER = False
Tenatst_MODE = False
LOCAL_Postgresql_Database = False
DEPLOYMENT_MODE = False

ALLOWED_HOSTS = (
    ['*'] if DEBUG else ['flip-cart-project-1.onrender.com']
)


# -----------------------------
# Installed Apps
# -----------------------------

SHARED_APPS = [
    # Tenant Core
    'django_tenants',
    'daphne',

    # Django Default Apps (MUST BE IN SHARED)
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'accounts',          # superadmin login / user creation
    'merchant_user',
    'django.contrib.admin',  # Admin should be shared for tenant management
    'django.contrib.staticfiles',

    # Third-party
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
    'django_elasticsearch_dsl',
    'django_elasticsearch_dsl_drf',
    'admin_thumbnails',

    # Your shared/local apps
   
    # 'delivery_user',
    # 'core',              # global config, landing page, etc.
]


TENANT_APPS = [
    # # Tenant-specific apps (data isolation)
    'category',          # each shop has its own categories
    'store',             # each shop has its own products
    'carts',             # per-tenant shopping carts
    'orders',            # each shop has separate orders
    # 'delivery_system',   # per-tenant delivery_system panel
    'seller_dashboard',  # per-tenant seller panel
    # 'orders_worker',     # per-tenant background order consumer
]

# -----------------------------
# django-tenants Config
# -----------------------------

# Important: Remove duplicates
INSTALLED_APPS = list(SHARED_APPS) + [app for app in TENANT_APPS if app not in SHARED_APPS]


# Tenant Model Configuration
TENANT_MODEL = "merchant_user.Organization"
TENANT_DOMAIN_MODEL = "merchant_user.OrganizationDomain"

# Tenant Database Router
DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

# Tenant Public Schema
PUBLIC_SCHEMA_NAME = 'public'

# Tenant Subdomain Settings
TENANT_SUBFOLDER_PREFIX = 'tenants'
# Or use subdomains:
TENANT_USES_SUBDOMAINS = True
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True


# -----------------------------
# Middleware
# -----------------------------
MIDDLEWARE = [
    # Django Tenants – must stay at the top
    'django_tenants.middleware.main.TenantMainMiddleware',

    # Security / CORS / Static
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    "whitenoise.middleware.WhiteNoiseMiddleware",

    # Core Middleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Custom Middleware for admin access control
      'flipcart_project.middleware.tenant_admin.TenantAdminMiddleware',
    # Tenant Admin Middleware

    # 'flipcart_project.middleware.tenant_admin.TenantAdminMiddleware',

    # Other Custom Middlewares (keep these after tenant admin)
    # 'flipcart_project.middleware.user_activity.UserActivityMiddleware',
    # 'flipcart_project.middleware.performance.PerformanceMiddleware',
    # 'flipcart_project.middleware.security.SecurityMiddleware',
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
                # 'category.context_processors.menu_links',
                # 'carts.context_processors.counter',
            ],
        },
    },
]

# -----------------------------
# Database
# -----------------------------
if DEBUG :
    # Localhost: PostgreSQL (django-tenants requires PostgreSQL)
    DATABASES = {
        'default': {
            'ENGINE': 'django_tenants.postgresql_backend',  # public schema migrate করার জন্য
            'NAME': 'GocartDB',
            'USER': 'postgres',
            'PASSWORD': '1234',
            'HOST': 'localhost',
            'PORT': '5432',
        }
    }


# elif DEBUG and USE_DOCKER:
#     # Localhost: Postgres (Docker)
#     DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': config('POSTGRES_DB', default='flipcart_db'),
#             'USER': config('POSTGRES_USER', default='flipcart_user'),
#             'PASSWORD': config('POSTGRES_PASSWORD', default='flipcart_pass'),
#             'HOST': config('POSTGRES_HOST', default='db'),
#             'PORT': config('POSTGRES_PORT', default='5432'),
#         }
#     }
# elif DEBUG and LOCAL_Postgresql_Database:
#         DATABASES = {
#         'default': {
#             'ENGINE': 'django.db.backends.postgresql',
#             'NAME': 'postgres',
#             'USER': 'postgres',
#             'PASSWORD': '1234',
#             'HOST': 'localhost',
#             'PORT': '5432',
            
#         }
#     }

# else:
#     # Production: Postgres (Render)
#     DATABASES = {
#         'default': dj_database_url.config(
#             default='postgresql://flip_data_user:hINuFmo29D1wMLpsFhEsTdTYQBSJiFbg@dpg-d2r8cqmr433s73fa64n0-a.oregon-postgres.render.com/flip_data'
#         )
#     }



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
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
}


# -----------------------------
# Simple JWT Config
# -----------------------------
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=15),  # short-lived access token
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),     # longer-lived refresh token
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),               # Authorization: Bearer <token>
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
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
TIME_ZONE = 'Asia/Dhaka'
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



# NGROK_URL = None
# CSRF_TRUSTED_ORIGINS = ['*']

if DEPLOYMENT_MODE:
    BASE_URL = NGROK_URL
    
else:
    if DEBUG:
        BASE_URL = "http://127.0.0.1:8000"
    else:
        BASE_URL= "https://flip-cart-project-1.onrender.com"

CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",  # React frontend
]

FRONTEND_URL = None
if  DEPLOYMENT_MODE:
    FRONTEND_URL = "https://flip-cart-project-frontend.onrender.com"
else:
    FRONTEND_URL = "http://localhost:3000"

# -----------------------------
# Redis Configuration (Smart Detection)
# -----------------------------
if USE_DOCKER:
    # Docker environment - use container names
    REDIS_HOST = 'redis'
    REDIS_PORT = 6379
    RABBITMQ_HOST = 'rabbitmq'  # যদি পরে rabbitmq add করেন
else:
    # Local development - use localhost
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    RABBITMQ_HOST = 'localhost'

REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}'

# CSRF_TRUSTED_ORIGINS.append(BASE_URL)
# -----------------------------
# Channels setup
# -----------------------------
ASGI_APPLICATION = 'flipcart_project.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}

# Point: Django cache (Redis) — use for caching analytics
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        }
    }
}

# -----------------------------
# Celery config
# -----------------------------

# CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'
if USE_DOCKER:
    CELERY_BROKER_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
else:
    CELERY_BROKER_URL = 'redis://127.0.0.1:6379/0'

CELERY_RESULT_BACKEND = f'redis://{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Dhaka'
CELERY_ENABLE_UTC = False
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'


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

# ----------------------------
# Point: RabbitMQ Configuration (Seller Events Queue)
# ----------------------------
RABBITMQ_SELLER_QUEUE = 'seller_events'
RABBITMQ_SELLER_EXCHANGE = 'seller_exchange'
RABBITMQ_SELLER_ROUTING_KEY = 'seller.event'


# ----------------------------
# Elasticsearch configuration
# ----------------------------

ELASTICSEARCH_OFFLINE = True 
ELASTICSEARCH_DEPLOY = False

if ELASTICSEARCH_OFFLINE:
    ELASTICSEARCH_DSL = {}
    
else:
    if ELASTICSEARCH_DEPLOY:

        ELASTICSEARCH_HOST = {
            'default': {
                'hosts': 'http://127.0.0.1:9200',
                'verify_certs': False,
            },
        }

        ELASTICSEARCH_DSL = {
            'default': {
                'hosts': 'http://127.0.0.1:9200',
                'verify_certs': False,
            },
        }
    else:
        ELASTICSEARCH_HOST = {
            'default': {
                'hosts': 'http://elasticsearch:9200',
                'verify_certs': False,
            },
        }

        ELASTICSEARCH_DSL = {
            'default': {
                'hosts': 'http://elasticsearch:9200',
                'verify_certs': False,
            },
        }

# ========================
# SSLCommerz Configuration
# ========================

SSLCZ_STORE_ID = "trans68369e6df24cb"
SSLCZ_STORE_PASS = "trans68369e6df24cb@ssl"
SSLCZ_IS_SANDBOX = True  # Set False in production






# ========================
# Stripe Plans Configuration
# ========================

STRIPE_PLANS = {
    'basic': {
        'name': 'Basic Plan',
        'price': 1999,  # $19.99 in cents
        'price_id': 'price_1PQAb2SAy6gqZ2y1X8X8X8X8',  # আপনার actual Stripe Price ID দিন
        'features': [
            'Up to 100 products', 
            'Basic analytics', 
            'Email support',
            'Standard delivery options'
        ]
    },
    'premium': {
        'name': 'Premium Plan',
        'price': 4999,  # $49.99 in cents  
        'price_id': 'price_1PQAb2SAy6gqZ2y1X8X8X8X9',  # আপনার actual Stripe Price ID দিন
        'features': [
            'Unlimited products',
            'Advanced analytics', 
            'Priority support',
            'Custom delivery options',
            'API access'
        ]
    },
    'enterprise': {
        'name': 'Enterprise Plan',
        'price': 9999,  # $99.99 in cents
        'price_id': 'price_1PQAb2SAy6gqZ2y1X8X8X8X0',  # আপনার actual Stripe Price ID দিন
        'features': [
            'Unlimited products',
            'Real-time analytics',
            '24/7 phone support',
            'Custom integrations',
            'Dedicated account manager'
        ]
    }
}

# ImageKit
IMAGEKIT_PUBLIC_KEY = "public_K/Li/QIxreloJJo5Xc4yG8So9X8="
IMAGEKIT_PRIVATE_KEY = "private_MlLDeuFx9gF6XWrRujo8h7Mklow="
IMAGEKIT_URL_ENDPOINT = "https://ik.imagekit.io/ehdyydeuq"



