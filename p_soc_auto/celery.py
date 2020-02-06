"""
p_soc_auto.celery
-----------------

This module contains the `Celery application
<https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html>`__
configuration.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
import os

from celery import Celery
from django.apps import apps
from django.conf import settings
from event_consumer.handlers import AMQPRetryConsumerStep

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p_soc_auto.settings.development')
os.environ.setdefault('EVENT_CONSUMER_APP_CONFIG', 'p_soc_auto.settings.development')
os.getenv('EVENT_CONSUMER_CONFIG_NAMESPACE', 'CELERY')

# the primary celery app
app = Celery('p_soc_auto')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.steps['consumer'].add(AMQPRetryConsumerStep)
app.autodiscover_tasks()
