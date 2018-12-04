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
os.environ.setdefault('EVENT_CONSUMER_APP_CONFIG', 'p_soc_auto.settings')
os.getenv('EVENT_CONSUMER_CONFIG_NAMESPACE', 'CELERY')

# the primary celery app
app = Celery('p_soc_auto')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.steps['consumer'].add(AMQPRetryConsumerStep)
app.autodiscover_tasks()
