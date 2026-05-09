import os
from pathlib import Path
from dotenv import load_dotenv
from celery.schedules import crontab

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
# import django.http.request
# _original = django.http.request.validate_host
# def _force_allow(host, allowed_hosts):
#     return True
# django.http.request.validate_host = _force_allow
ALLOWED_HOSTS = ['*', 'auth_service', 'auth_service:8001', 'localhost', '127.0.0.1']

CSRF_TRUSTED_ORIGINS = [
    'http://auth_service:8001',
    'http://localhost:8001',
    'http://127.0.0.1:8001',
]
USE_X_FORWARDED_HOST = True
USE_X_FORWARDED_PORT = True

INSTALLED_APPS = [
    'daphne',
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphene_django',
    'django_celery_beat',
    'corsheaders',
    'users',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'middleware.simple_middleware.SimpleMiddleware',
]

ROOT_URLCONF = 'auth_service.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'auth_service.wsgi.application'
ASGI_APPLICATION = 'auth_service.asgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME'),
        'USER': os.getenv('DB_USER'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST'),
        'PORT': os.getenv('DB_PORT'),
    }
}

AUTH_USER_MODEL = 'users.User'

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# JWT Settings (Pure PyJWT)
JWT_ALGORITHM = os.getenv('ALGORITHM', 'HS256')
JWT_ISSUER = os.getenv('JWT_ISSUER', 'my-app')
JWT_AUDIENCE = os.getenv('JWT_AUDIENCE', 'my-users')
ACCESS_TOKEN_LIFETIME = int(os.getenv('ACCESS_TOKEN_LIFETIME', 15))      # minutes
REFRESH_TOKEN_LIFETIME = int(os.getenv('REFRESH_TOKEN_LIFETIME', 7))     # days

# Email Settings
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Celery Settings
CELERY_BROKER_URL = os.getenv("REDIS_URL")
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_TIMEZONE = "Asia/Kolkata"

CELERY_BEAT_SCHEDULE = {
    "clean-expired-tokens-every-hour": {
        "task": "users.tasks.clean_expired_tokens",
        "schedule": crontab(minute=0, hour="*/1"),
    },
}

# Cache Settings (for rate limiting)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://redis:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Channels
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {"hosts": [os.getenv("REDIS_URL")]},
    },
}

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

# GraphQL Settings
GRAPHENE = {
    'SCHEMA': 'gql_schema.schema.schema',
    'MIDDLEWARE': [
        'gql_schema.middleware.AuthMiddleware',  # ← YAHAN
    ]
}
FRONTEND_URL = os.getenv("FRONTEND_URL")

# ========== PATCH: Allow underscore in hostname ==========
# from django.http.request import validate_host
# _original_validate_host = validate_host
# def _allow_underscore(host, allowed_hosts):
#     if host and '_' in host:
#         return True
#     return _original_validate_host(host, allowed_hosts)
# import django.http.request
# django.http.request.validate_host = _allow_underscore
# # ==========================================================


# Force allow all hosts
# import django.http.request
# def _allow_all(host, allowed_hosts):
#     return True
# django.http.request.validate_host = _allow_all

# FORCE ALLOW ALL HOSTS
# import django.http.request
# _original = django.http.request.validate_host
# def _force_allow(host, allowed_hosts):
#     return True
# django.http.request.validate_host = _force_allow

if os.getenv('ENVIRONMENT') == 'production':
    # Production: no patch, use ALLOWED_HOSTS
    ALLOWED_HOSTS = ['*', 'your-domain.com']
else:
    # Local: patch
    from django.http import HttpRequest
    HttpRequest.get_host = lambda self: 'localhost'