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
import socket
from datetime import timedelta
from logging import getLogger

from celery import group, shared_task
from django.apps import apps
from django.utils import timezone

from p_soc_auto_base import utils
from p_soc_auto_base.email import Email
from p_soc_auto_base.models import DeletionLog, Subscription

LOG = getLogger(__name__)


@shared_task(queue='data_prune')
def delete_records(model_name, age):
    LOG.info('Deleting records for model %s', model_name)

    try:
        model = apps.get_model(model_name)
    except utils.UnknownDataTargetError:
        LOG.exception('Cannot delete entries for non-existent model %s',
                      model)
        raise

    older_than = utils.MomentOfTime.past(**age)

    count_deleted = model.objects.filter(created__lte=older_than).all().delete()

    DeletionLog(model_name=str(model),
                records_deleted=count_deleted[0]).save()

    LOG.info('Deleted %s records from %s', count_deleted,
             model._meta.verbose_name)


@shared_task(queue='data_prune')
def group_deletions(models):
    LOG.info('Kicking off deletions')
    deletion_signatures = [delete_records.s(model_name, {'days': 3})
                           for model_name in models]
    group(deletion_signatures)()


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

    DeletionLog(model_name=str(email_model), records_deleted=count_deleted[0]).save()


#TODO allow passing in now
@shared_task(queue='shared')
def check_app_activity(hours, *app_pairs):
    # TODO offload these checks to the individual projects but call from here
    now = timezone.now()
    delta = timedelta(hours=hours)
    activity_pairs = []

    for app in app_pairs:
        model = apps.get_model(app['model'])

        try:
            latest = model.objects.latest()
        except model.DoesNotExist:
            latest_time = None
        else:
            latest_time = getattr(latest, app['column'])

        check = {f'{app["column"]}__gt': now - delta}
        count = len(model.objects.filter(**check))

        activity_pairs.append([app['name'], count, latest_time])

    def get_name(pair_array):
        return pair_array[0]

    sorted_pairs = sorted(activity_pairs, key=get_name)

    Email.send_email(None, Subscription.get_subscription('App Activity Update'),
                     activity_pairs=sorted_pairs,
                     machine=socket.gethostname(), hours=hours)

    for pair in activity_pairs:
        if pair[1] == 0:
            Email.send_email(
                None, Subscription.get_subscription('No Activity'),
                app_name=pair[0], hours=hours)
