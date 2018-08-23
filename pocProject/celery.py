from __future__ import absolute_import, unicode_literals
import os

from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pocProject.settings')

from django.conf import settings  # noqa

app = Celery('pocProject')

app.config_from_object('django.conf:settings')
app.autodiscover_tasks(lambda: settings.INSTALLED_APPS)
app.config_from_object('django.conf:settings', namespace='CELERY')
#app.autodiscover_tasks()

@app.task(bind=True)
def debug_task(self):
    """debug_task..."""
    print('Request: {0!r}'.format(self.request))
