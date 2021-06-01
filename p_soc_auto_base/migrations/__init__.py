"""
p_soc_auto_base.migrations
--------------------------

This module contains the migrations for `p_soc_auto_base`. That is migrations
that affect the SOC automation application, but do not belong in a specific
application.

:copyright:

    Copyright 2018 - 2020 Provincial Health Service Authority
    of British Columbia

"""
import pytz

from p_soc_auto_base.utils import get_or_create_user

TO_EMAILS = 'TSCST-Support@hssbc.ca,TSCST-Shiftmanager@hssbc.ca,' \
            'daniel.busto@hssbc.ca'


def create_subscription(apps, subscription_dict):
    """
    Saves a subscription to the database

    :param apps: Django apps instance.
    :param subscription_dict: arguments to set up a subscription, as a dict.
    """
    subscription_model = apps.get_model('p_soc_auto_base', 'Subscription')

    user = get_or_create_user()

    # TODO can I have alternate_email_subject='', do we even need the alt?
    subscription_defaults = {
        'emails_list': TO_EMAILS,
        'from_email': 'TSCST-Support@hssbc.ca',
        'template_dir': 'p_soc_auto_base/template/',
        'template_prefix': 'email/',
        'created_by_id': user.id,
        'updated_by_id': user.id,
        'enabled': True,
    }

    subscription_dict.update(subscription_defaults)

    subscription = subscription_model(**subscription_dict)

    subscription.save()


def create_task_objects(apps, cron_tasks=(), interval_tasks=()):
    """
    :param apps: The apps arg Django migrations uses to fetch models.
    :param cron_tasks: List of task dictionary, cron dictionary pairs. Task
                dictionary should include name, and task to run. Can optionally
                include arguments, and keyword arguments. Cron dictionary
                should include the hour and minutes to run the task. Assumes
                task will run on all days of the week, every week, all year.
                Also assumes local timezone (PT).
    :param interval_tasks: List of task dictionary, interval dictionary pairs.
                Task dictionary is the same as above. Interval dictionary
                should include period string (eg `'minutes'`) and an every
                integer (eg 5, when combined with the period `'minutes'` runs
                the task every 5 minutes)

    Creates periodic tasks based on the inputted dictionaries
    """
    crontab_model = apps.get_model('django_celery_beat', 'CrontabSchedule')
    interval_model = apps.get_model('django_celery_beat', 'IntervalSchedule')
    periodic_model = apps.get_model('django_celery_beat', 'PeriodicTask')

    timezone = pytz.timezone('America/Vancouver')

    # all our tasks run every day, all year
    # if a restriction on these is needed this code will have to be rewritten
    cron_defaults = {
        'day_of_week':   '*',
        'day_of_month':  '*',
        'month_of_year': '*',
        'timezone':      timezone,
    }

    # get_or_create prevents us from creating duplicate tasks
    for task_dict, cron_dict in cron_tasks:
        cron_dict.update(cron_defaults)
        cron, _ = crontab_model.objects.get_or_create(**cron_dict)

        task_dict['crontab'] = cron

        periodic_model.objects.get_or_create(**task_dict)

    for task_dict, interval_dict in interval_tasks:
        interval, _ = interval_model.objects.get_or_create(**interval_dict)

        task_dict['interval'] = interval

        periodic_model.objects.get_or_create(**task_dict)


def delete_tasks(apps, tasks):
    periodic_model = apps.get_model('django_celery_beat', 'PeriodicTask')

    periodic_model.objects.filter(name__in=[task['name'] for task, _ in tasks])\
        .delete()


def add_beats(cron=(), interval=()):
    def migration_function(apps, schema_editor):
        return create_task_objects(apps, cron, interval)

    return migration_function


def remove_beats(beats):
    def migration_function(apps, schema_editor):
        return delete_tasks(apps, beats)

    return migration_function
