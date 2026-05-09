import os
from pathlib import Path
from dotenv import load_dotenv
from mongoengine import connect

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-blog-key')
DEBUG = os.getenv('DEBUG', 'True') == 'True'
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'graphene_django',
    'corsheaders',
    'blogs',
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

ROOT_URLCONF = 'blog_service.urls'

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

WSGI_APPLICATION = 'blog_service.wsgi.application'

# ========== MONGODB CONNECTION (MONGOENGINE) ==========
MONGO_HOST = os.getenv('MONGO_HOST', 'mongo_blog')
MONGO_PORT = int(os.getenv('MONGO_PORT', 27018))
MONGO_DB_NAME = os.getenv('MONGO_DB_NAME', 'blog_db')

try:
    connect(
        db=MONGO_DB_NAME,
        host=MONGO_HOST,
        port=MONGO_PORT,
        alias='default'
    )
    print(f"✅ Connected to MongoDB: {MONGO_HOST}:{MONGO_PORT}/{MONGO_DB_NAME}")
except Exception as e:
    print(f"❌ MongoDB connection failed: {e}")

# Django still needs a DATABASES setting (dummy)
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.dummy',
    }
}

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
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True

GRAPHENE = {
    'SCHEMA': 'gql_schema.schema.schema',
    'MIDDLEWARE': [
        'gql_schema.middleware.AuthMiddleware',
    ]
}

JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-jwt-secret-key')
JWT_ALGORITHM = os.getenv('JWT_ALGORITHM', 'HS256')

if os.getenv('ENVIRONMENT') == 'production':
    # Production: no patch, use ALLOWED_HOSTS
    ALLOWED_HOSTS = ['*', 'your-domain.com']
else:
    # Local: patch
    from django.http import HttpRequest
    HttpRequest.get_host = lambda self: 'localhost'