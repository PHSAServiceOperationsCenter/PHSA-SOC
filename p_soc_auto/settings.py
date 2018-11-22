"""
.. _settings

Django settings for p_soc_auto project.

Generated by 'django-admin startproject' using Django 2.0.7.

For more information on this file, see
https://docs.djangoproject.com/en/2.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.0/ref/settings/

:module:     p_soc_auto.settings

:contact:    ali.rahmat@phsa.ca
:contact:    serban.teodorescu@phsa.ca

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia
"""

import os

from django.utils import timezone
from kombu import Queue, Exchange


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = '5u7)@@#z0yr-$4q#enfc&20a6u6u-h1_nr^(z%fkqu3dx+y6ji'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['*', ]

ADMINS = [('Serban Teodorescu', 'serban.teodorescu@phsa.ca'), ]

# logging
LOG_DIR = os.path.join(BASE_DIR, 'logs')
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format':
            '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
    'handlers': {
        'django_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'django.log'),
            'formatter': 'verbose',
            'filters': ['require_debug_true']
        },
        'ssl_cert_tracker_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'ssl_cert_tracker.log'),
            'formatter': 'verbose',
            'filters': ['require_debug_true']
        },
        'console': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'simple'
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['django_log'],
            'level': 'DEBUG',
            'propagate': True,
        },
        'ssl_cert_tracker': {
            'handlers': ['ssl_cert_tracker_log', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Application definition
INSTALLED_APPS = [
    'rules_engine.apps.RulesEngineConfig',
    'orion_integration.apps.OrionIntegrationConfig',
    'p_soc_auto_base.apps.PSocAutoBaseConfig',
    'ssl_cert_tracker.apps.SslCertificatesConfig',
    'notifications.apps.NotificationsConfig',
    'citrus_borg.apps.CitrusBorgConfig',
    'simple_history',
    'dal',
    'dal_select2',
    'grappelli',
    'rangefilter',
    'templated_email',
    'django.contrib.admin',
    'django.contrib.admindocs',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_celery_beat',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.contrib.admindocs.middleware.XViewMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'simple_history.middleware.HistoryRequestMiddleware',
]

ROOT_URLCONF = 'p_soc_auto.urls'

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

WSGI_APPLICATION = 'p_soc_auto.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'phsa_database',
        'HOST': '',
        'PASSWORD': 'phsa_db_password',
        'USER': 'phsa_db_user',
    }
}


# Password validation
# https://docs.djangoproject.com/en/2.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/2.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Vancouver'

USE_I18N = True

USE_L10N = True

USE_TZ = True


STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
STATIC_URL = '/static/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media/')
MEDIA_URL = '/media/'

# orion logins
ORION_ENTITY_URL = 'https://orion.vch.ca'
ORION_URL = 'https://orion.vch.ca:17778/SolarWinds/InformationService/v3/Json'
ORION_USER = 'CSTmonitor'
ORION_PASSWORD = 'phsa123'
ORION_VERIFY_SSL_CERT = False
ORION_TIMEOUT = (10.0, 22.0)
"""
:var ORION_TIMEOUT: the timeouts used by the `requests` module

    the values in the tuple are in seconds; the first value is the connection
    timeout, the second one is the read tiemout

"""

# celery settings (use namespace='CELERY')
CELERY_BROKER_URL = 'amqp://guest:guest@localhost//'

CELERY_ACCEPT_CONTENT = ['json', 'pickle']
CELERY_RESULT_BACKEND = 'rpc://'
CELERY_RESULT_PERSISTENT = False
CELERY_TASK_SERIALIZER = 'json'

CELERY_QUEUES = (
    Queue('rules', Exchange('rules'), routing_key='rules'),
    Queue('email', Exchange('email'), routing_key='email'),
    Queue('orion', Exchange('orion'), routing_key='orion'),
    Queue('nmap', Exchange('nmap'), routing_key='nmap'),
    Queue('ssl', Exchange('ssl'), routing_key='ssl'),
    Queue('shared', Exchange('shared'), routing_key='shared'),
    Queue('citrus_borg', Exchange('the_borg'), routing_key='citrus_borg')
)

CELERY_DEFAULT_QUEUE = 'shared'
CELERY_DEFAULT_EXCHANGE = 'shared'
CELERY_DEFAULT_ROUTING_KEY = 'shared'

# event consumer settings (use namespace='EVENT_CONSUMER'
CELERY_USE_DJANGO = True
CELERY_EXCHANGES = {
    'default': {'name': 'logstash', 'type': 'topic', },
}


# service users
RULES_ENGINE_SERVICE_USER = 'phsa_rules_user'
NOTIFICATIONS_SERVICE_USER = 'phsa_notifications_user'


# common email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# EMAIL_BACKEND = 'django.core.mail.backends.filebased.EmailBackend'
EMAIL_FILE_PATH = '/tmp'
EMAIL_HOST = 'smtp.healthbc.org'
EMAIL_USE_TLS = False
EMAIL_USE_SSL = False
EMAIL_PORT = 25
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
DEFAULT_FROM_EMAIL = ['TSCST-Support@hssbc.ca']
DEFAULT_EMAIL_REPLY_TO = DEFAULT_FROM_EMAIL
SUB_EMAIL_TYPE = 0
ESC_EMAIL_TYPE = 1
SUB_ESC_EMAIL_TYPE = 2

#=========================================================================
# # email settings for gmail
# # these will not work from 10.1.80.0
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_HOST_USER = 'phsadev@gmail.com'
# EMAIL_HOST_PASSWORD = 'gaukscylgzzlavva'
#=========================================================================

# broadcast only notifications of these levels
NOTIFICATION_BROADCAST_LEVELS = []

# server port
SERVER_PORT = '8080'

# settings specific to the citrus_borg application
CITRUS_BORG_SERVICE_USER = 'citrus-borg'
CITRUS_BORG_EVENTS_EXPIRE_AFTER = timezone.timedelta(hours=72)
CITRUS_BORG_DELETE_EXPIRED = True
CITRUS_BORG_BROKER_LAST_SEEN_ALARM_AFTER = '1 hour'
CITRUS_BORG_YELLOW_LOGON_ALARM = 'more than X in Y interval'
CITRUS_BORG_RED_LOGON_ALARM = 'X in a row'
CITRUS_BORG_EVENT_ANALYSIS_EVERY = 'to be determined'
