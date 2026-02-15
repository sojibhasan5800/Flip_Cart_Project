# flipcart_project/settings/production.py
from flipcart_project.settings import *


DEBUG = False
ALLOWED_HOSTS = ['flip-cart-project-1.onrender.com']

DATABASES = {
    'default': dj_database_url.config(default='postgresql://flip_data_user:hINuFmo29D1wMLpsFhEsTdTYQBSJiFbg@dpg-d2r8cqmr433s73fa64n0-a.oregon-postgres.render.com/flip_data')
}

SECRET_KEY = config('SECRET_KEY')  # .env বা Render এ সেট করো

REDIS_HOST = config('REDIS_HOST')
REDIS_PORT = config('REDIS_PORT', cast=int)
REDIS_URL = f'redis://{REDIS_HOST}:{REDIS_PORT}'

CHANNEL_LAYERS['default']['CONFIG']['hosts'] = [(REDIS_HOST, REDIS_PORT)]
CACHES['default']['LOCATION'] = f"{REDIS_URL}/1"
CELERY_BROKER_URL = f'{REDIS_URL}/0'
CELERY_RESULT_BACKEND = f'{REDIS_URL}/1'

BASE_URL = "https://flip-cart-project-1.onrender.com"
FRONTEND_URL = "https://flip-cart-project-frontend.onrender.com"

SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Cloudinary (uncomment করো production এ)
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': 'dwemgnaux',
    'API_KEY': '986429826285289',
    'API_SECRET': '3-_GLoBXW5SvXyCNPrbv4-QGDgg',
}
DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'