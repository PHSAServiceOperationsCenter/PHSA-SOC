import os
from celery import Celery
from django.apps import apps
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'p_soc_auto.settings')

app = Celery('p_soc_auto')

app.config_from_object('django.conf:settings', namespace='CELERY')

app.autodiscover_tasks()
