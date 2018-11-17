"""
.. _celery:

celery applications configuration

:module:    p_soc_auto.celery

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    nov. 16, 2018

"""
import os

from celery import Celery
from django.apps import apps
from django.conf import settings
from event_consumer.handlers import AMQPRetryConsumerStep

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p_soc_auto.settings')

# the primary celery app
app = Celery('p_soc_auto')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

# the celery app that provides consumers
consumer_app = Celery('p_soc_auto')
consumer_app.config_from_object(
    'django.conf:settings', namespace='EVENT_CONSUMER')
consumer_app.autodiscover_tasks()
