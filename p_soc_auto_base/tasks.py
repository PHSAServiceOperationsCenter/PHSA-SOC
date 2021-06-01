"""
p_soc_auto.tasks
----------------

This module contains `Celery tasks
<https://docs.celeryproject.org/en/latest/userguide/tasks.html>`__ that do not
have a more specific location to be.

:copyright:

    Copyright 2020- Provincial Health Service Authority
    of British Columbia

"""
import socket
from datetime import timedelta
from logging import getLogger

from celery import group, shared_task
from p_soc_auto_base.preferences import get_preference
from django.apps import apps
from django.utils import timezone
from django_celery_beat.models import PeriodicTask

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
def check_app_activity(hours, *apps_to_monitor):
    # TODO offload these checks to the individual projects but call from here
    now = timezone.now()
    delta = timedelta(hours=hours)
    activity_pairs = []

    for app in apps_to_monitor:
        print(app)
        model = apps.get_model(app)

        try:
            latest = model.objects.latest()
        except model.DoesNotExist:
            latest_time = None
        else:
            latest_time = getattr(latest, model._meta.get_latest_by)

        check = {f'{model._meta.get_latest_by}__gt': now - delta}
        count = len(model.objects.filter(**check))

        try:
            gen_tasks = PeriodicTask.objects.filter(task__contains=model.gen_func_name, enabled=True)
            if gen_tasks.count() != 1:
                raise Exception(f'Found {gen_tasks.count()} tasks for {model.gen_func_name}. Cannot provide schedule if there is not a single cannonical task.')
            cannonical_task = gen_tasks.first()
            # only one of the schedules can be set so using or here is fine
            schedule_wrapper = (cannonical_task.interval
                               or cannonical_task.crontab
                               or cannonical_task.solar
                               or cannonical_task.clocked)
        except AttributeError:
            # couldn't find the generator in registry, no schedule to find
            schedule_wrapper = None

        # TODO do some sort of thing to set is_due when there is no schedule
        is_due = not latest_time

        if latest_time:
            if not schedule_wrapper:
                delta = get_external_task_schedule()
                is_due = latest_time < timezone.now() - delta
            else:
                is_due = schedule_wrapper.schedule.is_due(latest_time)

        activity_pairs.append({
            'is_due': is_due,
            'model': model._meta.verbose_name,
            'count': count,
            'latest': latest_time,
            'schedule': schedule_wrapper or "Set externally"
        })

        if is_due:
            if schedule_wrapper:
                schedule_str = schedule_wrapper.schedule.run_every
            else:
                schedule_str = get_external_task_schedule()

            schedule_str = timezone.now() - schedule_str

            Email.send_email(None, Subscription.get_subscription('No Activity'),
                app_name=model._meta.verbose_name, schedule=schedule_str)

    def get_name(pair_array):
        return pair_array['model']

    sorted_pairs = sorted(activity_pairs, key=get_name)

    Email.send_email(None, Subscription.get_subscription('App Activity Update'),
                     activity_pairs=sorted_pairs,
                     machine=socket.gethostname(), hours=hours)


def get_external_task_schedule():
    return timedelta(**{get_preference('commonalertargs__external_task_period'):
                        get_preference('commonalertargs__external_task_every')})
