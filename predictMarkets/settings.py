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

ALLOWED_HOSTS = ['predict-markets.herokuapp.com', '66.96.162.150', 'chatnun.com', 'www.chatnun.com']


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
        'NAME': 'd7f8rqmt3g6vk6',
        'USER': 'tgjmzvivuenzpj',
        'PASSWORD': 'ce5308e80b98ffa36c801aa819faac8d4f17729db81a2bf5fa613329cc0c5f32',
        'HOST': 'ec2-3-218-171-44.compute-1.amazonaws.com',
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

AUTHENTICATION_BACKENDS = (
    'django.contrib.auth.backends.ModelBackend', 
    'allauth.account.auth_backends.AuthenticationBackend', # default auth backend
)
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': '691697894973-33buj89dqi001sd9e2v0f4hvouko1hqp.apps.googleusercontent.com',
            'secret': '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',
            'key': ''
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
            'client_id': '6c07376d-c35b-4141-9893-91c8ba379b6a',
            'secret': 'aLd8Q~w4cgoeCq~HIxy5jTH5gtEmB-x9DU3IDcfw',
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

# SITE_ID = 1

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
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

# Set the bucket name
AWS_STORAGE_BUCKET_NAME = 'bucketeer-b065505d-e62c-48c1-aa48-89f10be11f06'

# Set the AWS access keys (replace with your own credentials)
AWS_ACCESS_KEY_ID = 'AKIARVGPJVYVEQ2BFMNR'
AWS_SECRET_ACCESS_KEY = 'NVdhrQDI/RuxtGLX2f0TSUVi7ut2ATCRlz6BgNXa'

# Set the static and media URLs
STATIC_URL = '/static/'
MEDIA_URL = '/media/'

# Set the static and media root directories
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Set the static and media file storage locations
STATICFILES_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'
DEFAULT_FILE_STORAGE = 'storages.backends.s3boto3.S3Boto3Storage'

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'contact@chatnun.com' # Replace with your email address
EMAIL_HOST_PASSWORD = 'Ghadi03@' # Replace with your email password
EMAIL_USE_OAUTH = True
EMAIL_CLIENT_ID = '844297491487-6emc7ua3op90mil7so3rbct2uo9sec4c.apps.googleusercontent.com'  # Obtained from the downloaded credentials file
EMAIL_CLIENT_SECRET = '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'  # Obtained from the downloaded credentials file
EMAIL_REFRESH_TOKEN = '1//04CvSYqLBFOyrCgYIARAAGAQSNwF-L9IrZTg74zVRefuQPo0qXZTWPK7GC4dWsQa_QXeblSMXHCQT-27RPkeaS9FwpLL5iYZDr84'
# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'localhost'
# EMAIL_PORT = 1025
# EMAIL_USE_TLS = False
# DEFAULT_FROM_EMAIL = 'noreply@example.com'

# EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_HOST = 'sandbox.smtp.mailtrap.io'
# EMAIL_HOST_USER = 'b73eb5816e9cfc'
# EMAIL_HOST_PASSWORD = '77774fb61fa88b'
# EMAIL_PORT = '2525'
# EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False

# CELERY_BROKER_URL = 'redis://localhost:6379'
# CELERY_ACCEPT_CONTENT = ['json']
# CELERY_TASK_SERIALIZER = 'json'
# CELERY_RESULT_SERIALIZER = 'json'

# MESSAGE_STORAGE = 'django.contrib.messages.storage.session.SessionStorage'
# django_heroku.settings(locals())
# SENDGRID_API_KEY='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'
# EMAIL_BACKEND = 'sgbackend.SendGridBackend'
# OPENAI_API_KEY = "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"

LOCATION_FIELD_PATH = STATIC_URL + 'location_field'
LOCATION_FIELD = {
'map.provider': 'openstreetmap',
}
AUTH_USER_MODEL = 'myapp.User'
ADMIN_EMAIL = 'contact@chatnun.com'
LANGUAGE_COOKIE_NAME = 'django_language'

STRIPE_PUBLISHABLE_KEY = 'pk_live_51MvUwGCTZjMJ7NHQCedzVz1S81Wu4lfjKPk95ZhphhLZjkkbzEctYPw5XX9z8AuN89LBMkpqj45LtR7tpAM6oySr00Tf6XV6q9'
STRIPE_SECRET_KEY = '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'
STRIPE_PRICE_3MONTHS = 'price_1N3jftCTZjMJ7NHQflijKnX1'
STRIPE_PRICE_6MONTHS = 'price_1N3jftCTZjMJ7NHQkG1bZGvP'
STRIPE_PRICE_1YEAR = 'price_1N3jftCTZjMJ7NHQt9GXAzSK'

