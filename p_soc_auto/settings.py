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
        'orion_flash_log': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': os.path.join(LOG_DIR, 'orion_flash.log'),
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
        'orion_flash': {
            'handlers': ['orion_flash_log', 'console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.PyLibMCCache',
        'LOCATION': [
            '127.0.0.1:11211',
        ]
    }
}

# Application definition
INSTALLED_APPS = [
    #    'rules_engine.apps.RulesEngineConfig',
    'orion_integration.apps.OrionIntegrationConfig',
    'p_soc_auto_base.apps.PSocAutoBaseConfig',
    'ssl_cert_tracker.apps.SslCertificatesConfig',
    #    'notifications.apps.NotificationsConfig',
    'citrus_borg.apps.CitrusBorgConfig',
    'orion_flash.apps.OrionFlashConfig',
    'simple_history',
    'dal',
    'dal_select2',
    'rangefilter',
    'templated_email',
    'timedeltatemplatefilter',
    'dynamic_preferences',
    #    'dynamic_preferences.users.apps.UserPreferencesConfig',
    'grappelli',
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
                'dynamic_preferences.processors.global_preferences',
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
    },
    'orion_aux_db': {
        'ENGINE': 'sql_server.pyodbc',
        'NAME': 'orion_aux_db',
        'USER': 'orion_aux_db_user',
        'PASSWORD': 'orion_aux_db_password',
        #	'SA_PASSWORD': "orion_aux_db_password123',
        'HOST': '10.248.211.70',
        # 'HOST': '10.66.6.9',
        'PORT': '',

        'OPTIONS': {
            'driver': 'ODBC Driver 17 for SQL Server',
        },
    },
}

DATABASE_ROUTERS = ['orion_flash.router.OrionAuxRouter', ]

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
ORION_HOSTNAME = 'orion.vch.ca'
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
ORION_RETRY = 3
ORION_BACKOFF_FACTOR = 0.3

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
    Queue('citrus_borg', Exchange('the_borg'), routing_key='citrus_borg'),
    Queue('borg_chat', Exchange('the_borg'), routing_key='borg_chat'),
    Queue('orion_flash', Exchange('orion_flash'), routing_key='orion_flash'),
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
DEFAULT_FROM_EMAIL = 'TSCST-Support@hssbc.ca'
DEFAULT_EMAIL_REPLY_TO = DEFAULT_FROM_EMAIL
SUB_EMAIL_TYPE = 0
ESC_EMAIL_TYPE = 1
SUB_ESC_EMAIL_TYPE = 2

# =========================================================================
# # email settings for gmail
# # these will not work from 10.1.80.0
# EMAIL_HOST = 'smtp.gmail.com'
# EMAIL_USE_TLS = True
# EMAIL_USE_SSL = False
# EMAIL_PORT = 587
# EMAIL_HOST_USER = 'phsadev@gmail.com'
# EMAIL_HOST_PASSWORD = 'gaukscylgzzlavva'
# =========================================================================

# broadcast only notifications of these levels
NOTIFICATION_BROADCAST_LEVELS = []

# server settings: use them to build URL's
SERVER_PORT = '8080'
SERVER_PROTO = 'http'

# settings specific to the citrus_borg application
CITRUS_BORG_SERVICE_USER = 'citrus-borg'
CITRUS_BORG_DEAD_BOT_AFTER = timezone.timedelta(minutes=10)
CITRUS_BORG_DEAD_SITE_AFTER = timezone.timedelta(minutes=10)
CITRUS_BORG_DEAD_BROKER_AFTER = timezone.timedelta(hours=24)
CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER = timezone.timedelta(hours=72)
CITRUS_BORG_IGNORE_EVENTS_OLDER_THAN = timezone.timedelta(hours=72)
CITRUS_BORG_EVENTS_EXPIRE_AFTER = timezone.timedelta(hours=72)
CITRUS_BORG_DELETE_EXPIRED = True
CITRUS_BORG_FAILED_LOGON_ALERT_INTERVAL = timezone.timedelta(minutes=10)
CITRUS_BORG_FAILED_LOGON_ALERT_THRESHOLD = 2
CITRUS_BORG_SITE_UX_REPORTING_PERIOD = timezone.timedelta(hours=24)
CITRUS_BORG_UX_ALERT_THRESHOLD = timezone.timedelta(seconds=10)
CITRUS_BORG_UX_ALERT_INTERVAL = timezone.timedelta(minutes=10)
CITRUS_BORG_FAILED_LOGONS_PERIOD = timezone.timedelta(hours=12)
CITRUS_BORG_NO_NEWS_IS_GOOD_NEWS = False

DYNAMIC_PREFERENCES = {
    'MANAGER_ATTRIBUTE': 'preferences',
    'REGISTRY_MODULE': 'dynamic_preferences_registry',
    'ADMIN_ENABLE_CHANGELIST_FORM': True,
    'SECTION_KEY_SEPARATOR': '__',
    'ENABLE_CACHE': True,
    'VALIDATE_NAMES': True,
}

NMAP_SERVICE_USER = 'nmap_user'

SSL_PROBE_OPTIONS = '-Pn -p %s --script ssl-cert'
SSL_DEFAULT_PORT = 443
