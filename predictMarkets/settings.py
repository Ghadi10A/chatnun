"""
Django settings for predictMarkets project.
 
Generated by 'django-admin startproject' using Django 4.1.4.

For more information on this file, see  
https://docs.djangoproject.com/en/4.1/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.1/ref/settings/
"""
import dj_database_url
import django_heroku
from pathlib import Path
import os
from django.utils.translation import gettext_lazy as _
from decouple import config
from django_redis.cache import RedisCache
import boto3
from storages.backends.s3boto3 import S3Boto3Storage

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent



# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY') 

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True
#DEBUG = config('DEBUG', cast=bool)
#PREPEND_WWW = True
#BASE_URL = "****************"
ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'myapp',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages', 
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',
    'django_extensions',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'allauth.socialaccount.providers.microsoft',
    'modeltranslation',
    'django_bootstrap_icons',
    'location_field.apps.DefaultConfig',
    'channels',
    'myapp.notifications',
    'django.contrib.humanize',
    'emojis',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'predictMarkets.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['myapp/templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.i18n',
            ],
        },
    },
]

WSGI_APPLICATION = 'predictMarkets.wsgi.application'
ASGI_APPLICATION = 'predictMarkets.asgi.application'

# Database
# https://docs.djangoproject.com/en/4.1/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': '************',
        'USER': '************',
        'PASSWORD': '****************',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}


# myproject/settings.py

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer',
    },
}


# Password validation
# https://docs.djangoproject.com/en/4.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]
SITE_ID = 1
AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', 
    'allauth.account.auth_backends.AuthenticationBackend', # default auth backend
)
LOGIN_REDIRECT_URL = '/'
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': '**************************',
            'secret': '*****************************',
            'key': '********************************'
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    'microsoft': {
        'APP': {
            'client_id': '***********************',
            'secret': '**************************',
            'tenant': 'common',  # Use 'common' for multi-tenant apps
        },
        'SCOPE': [
            'openid',
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'response_type': 'code',
        },
    }
}
SOCIALACCOUNT_AUTO_SIGNUP = True

# 

# Internationalization
# https://docs.djangoproject.com/en/4.1/topics/i18n/


LANGUAGE_CODE = 'en-us'

LOCALE_PATHS = [
    os.path.join(BASE_DIR, 'myapp', 'local'),
]

LANGUAGES = [
    ('ar', 'Arabic'),
    ('en', 'English'),
    ('tr', 'Turkish'),
    ('fr', 'French'),
    ('es', 'Spanish'),
]

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.1/howto/static-files/
# Configure storage backend
DEFAULT_FILE_STORAGE = '*********************'
DEFAULT_CHARSET = 'utf-8'
# Set the bucket name
AWS_STORAGE_BUCKET_NAME = '*********************'

# Set the AWS access keys (replace with your own credentials)
AWS_ACCESS_KEY_ID = '********************'
AWS_SECRET_ACCESS_KEY = '*****************'

# Set the static and media URLs
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Set the static and media root directories
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Set the static and media file storage locations
STATICFILES_STORAGE = '********************'
DEFAULT_FILE_STORAGE = '*******************'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'contact@******.com' # Replace with your email address
EMAIL_HOST_PASSWORD = '*********' # Replace with your email password
EMAIL_USE_OAUTH = True
EMAIL_CLIENT_ID = '**************************'  # Obtained from the downloaded credentials file
EMAIL_CLIENT_SECRET = '**********************'  # Obtained from the downloaded credentials file
EMAIL_REFRESH_TOKEN = '**********************'
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 1025
# EMAIL_USE_TLS = False
# DEFAULT_FROM_EMAIL = 'noreply@example.com'

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
# EMAIL_HOST_USER = '***********'
# EMAIL_HOST_PASSWORD = '**************'
# EMAIL_PORT = '2525'
# EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False

# CELERY_BROKER_URL = 'redis://localhost:6379'
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'

# MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
# django_heroku.settings(locals())
# SENDGRID_API_KEY='*********************'
# EMAIL_BACKEND = 'sgbackend.SendGridBackend'
# OPENAI_API_KEY = "***********************"

LOCATION_FIELD_PATH = STATIC_URL + 'location_field'
LOCATION_FIELD = {
'map.provider': 'openstreetmap',
}
ADMIN_EMAIL = 'contact@***********.com'
LANGUAGE_COOKIE_NAME = 'django_language'

STRIPE_PUBLISHABLE_KEY = '********************************************************************************************************'
STRIPE_SECRET_KEY = '*************************************************************************************************************'
STRIPE_PRICE_3MONTHS = '******************************'
STRIPE_PRICE_6MONTHS = '******************************'
STRIPE_PRICE_1YEAR = '********************************'

