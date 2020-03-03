"""
p_soc_auto.tasks
----------------

This module contains `Celery tasks
<https://docs.celeryproject.org/en/latest/userguide/tasks.html>`__ that do not
have a more specific location to be.

:copyright:

    Copyright 2020- Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from logging import getLogger

from celery import shared_task
from django.apps import apps

from p_soc_auto_base import utils

LOG = getLogger(__name__)


@shared_task(queue='data_prune')
def delete_emails(**age):
    """
    Deletes emails saved by the templated_email app which are older than the
    inputted age

    :arg age: named arguments that can be used for creating a
        :class:`datetime.timedelta` object

        See `Python docs for timedelta objects
        <https://docs.python.org/3.6/library/datetime.html#timedelta-objects>`__
    """
    email_model = apps.get_model('templated_email.SavedEmail')

    older_than = utils.MomentOfTime.past(**age)

    count_deleted = email_model.objects.filter(created__lte=older_than).\
        delete()

    LOG.info('Deleted %s emails created earlier than %s.', count_deleted,
             older_than.isoformat())
