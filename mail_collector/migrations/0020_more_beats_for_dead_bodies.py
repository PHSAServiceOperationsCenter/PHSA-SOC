# Generated by Django 2.1.4 on 2019-06-20 20:49
import pytz

from django.db import migrations


def add_beats(apps, schema_editor):
    timezone = pytz.timezone('America/Vancouver')

    periodic_tasks = [
        {
            'name': ('Raise critical  alert for exchange servers'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_updated__lte",'
                '"Exchange Servers Not Seen"]'),
            'kwargs': (
                '{"url_annotate": false,'
                '"level": "CRITICAL",'
                '"filter_pref": "exchange__server_error","enabled": true}'),
            'interval': {
                'every': 30,
                'period': 'minutes',
            },
        },
        {
            'name': ('Raise critical  alert for connections to exchange servers'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_connection__lte",'
                '"Exchange Servers No Connection"]'),
            'kwargs': (
                '{"url_annotate": false,'
                '"level": "CRITICAL",'
                '"filter_pref": "exchange__server_error","enabled": true}'),
            'interval': {
                'every': 30,
                'period': 'minutes',
            },
        },
        {
            'name': ('Raise warning  alert for connections to exchange servers'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_connection__lte",'
                '"Exchange Servers No Connection"]'),
            'kwargs': (
                '{"url_annotate": false,'
                '"level": "WARNING",'
                '"filter_pref": "exchange__server_warn","enabled": true}'),
            'interval': {
                'every': 30,
                'period': 'minutes',
            },
        },
        {
            'name': ('Raise critical  alert for send to exchange servers'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_send__lte",'
                '"Exchange Servers No Send"]'),
            'kwargs': (
                '{"url_annotate": false,'
                '"level": "CRITICAL",'
                '"filter_pref": "exchange__server_error","enabled": true}'),
            'interval': {
                'every': 30,
                'period': 'minutes',
            },
        },
        {
            'name': ('Raise warning  alert for send to exchange servers'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_send__lte",'
                '"Exchange Servers No Send"]'),
            'kwargs': (
                '{"url_annotate": false,'
                '"level": "WARNING",'
                '"filter_pref": "exchange__server_warn","enabled": true}'),
            'interval': {
                'every': 30,
                'period': 'minutes',
            },
        },
        {
            'name': ('Raise critical  alert for receive to exchange servers'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_inbox_access__lte",'
                '"Exchange Servers No Receive"]'),
            'kwargs': (
                '{"url_annotate": false,'
                '"level": "CRITICAL",'
                '"filter_pref": "exchange__server_error","enabled": true}'),
            'interval': {
                'every': 30,
                'period': 'minutes',
            },
        },
        {
            'name': ('Raise warning  alert for receive to exchange servers'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_inbox_access__lte",'
                '"Exchange Servers No Receive"]'),
            'kwargs': (
                '{"url_annotate": false,'
                '"level": "WARNING",'
                '"filter_pref": "exchange__server_warn","enabled": true}'),
            'interval': {
                'every': 30,
                'period': 'minutes',
            },
        },
        {
            'name': ('Raise critical  alert for exchange databases'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangedatabases","last_access__lte",'
                '"Exchange Databases Not Seen"]'),
            'kwargs': (
                '{"url_annotate": false,'
                '"level": "CRITICAL",'
                '"filter_pref": "exchange__server_error","enabled": true}'),
            'interval': {
                'every': 30,
                'period': 'minutes',
            },
        },
        {
            'name': ('Raise warning  alert for exchange databases'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangedatabase","last_access__lte",'
                '"Exchange Databases Not Seen"]'),
            'kwargs': (
                '{"url_annotate": false,'
                '"level": "WARNING",'
                '"filter_pref": "exchange__server_warn","enabled": true}'),
            'interval': {
                'every': 30,
                'period': 'minutes',
            },
        },

    ]

    cron_tasks = [
        {
            'name': ('No connect exchange servers report'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_connection__lte",'
                '"Exchange Servers No Connection"]'),
            'kwargs': (
                '{"url_annotate": true,'
                '"level": null,'
                '"filter_pref": "exchange__report_interval","enabled": true}'),
            'crontab': {
                'minute': '45',
                'hour': '07,15,23',
                'day_of_week': '*',
                'day_of_month': '*',
                'month_of_year': '*',
                'timezone': timezone,
            },
        },
        {
            'name': ('No send exchange servers report'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_send__lte",'
                '"Exchange Servers No Send"]'),
            'kwargs': (
                '{"url_annotate": true,'
                '"level": null,'
                '"filter_pref": "exchange__report_interval","enabled": true}'),
            'crontab': {
                'minute': '45',
                'hour': '07,15,23',
                'day_of_week': '*',
                'day_of_month': '*',
                'month_of_year': '*',
                'timezone': timezone,
            },
        },
        {
            'name': ('No receive exchange servers report'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_inbox_access__lte",'
                '"Exchange Servers No Receive"]'),
            'kwargs': (
                '{"url_annotate": true,'
                '"level": null,'
                '"filter_pref": "exchange__report_interval","enabled": true}'),
            'crontab': {
                'minute': '45',
                'hour': '07,15,23',
                'day_of_week': '*',
                'day_of_month': '*',
                'month_of_year': '*',
                'timezone': timezone,
            },
        },
        {
            'name': ('Dead exchange databases report'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangedatabase","last_access__lte",'
                '"Exchange Databases Not Seen"]'),
            'kwargs': (
                '{"url_annotate": true,'
                '"level": null,'
                '"filter_pref": "exchange__report_interval","enabled": true}'),
            'crontab': {
                'minute': '45',
                'hour': '07,15,23',
                'day_of_week': '*',
                'day_of_month': '*',
                'month_of_year': '*',
                'timezone': timezone,
            },
        },


    ]

    CrontabSchedule = apps.get_model('django_celery_beat', 'CrontabSchedule')
    IntervalSchedule = apps.get_model(
        'django_celery_beat', 'IntervalSchedule')
    PeriodicTask = apps.get_model('django_celery_beat', 'PeriodicTask')

    for _task in cron_tasks:
        cron, _ = CrontabSchedule.objects.get_or_create(**_task['crontab'])

        _task['crontab'] = cron

        PeriodicTask.objects.create(**_task)

    for _task in periodic_tasks:
        interval, _ = IntervalSchedule.objects.get_or_create(
            **_task['interval'])

        _task['interval'] = interval

        PeriodicTask.objects.create(**_task)


class Migration(migrations.Migration):

    dependencies = [
        ('mail_collector', '0018_add_beats_for_dead_bodies'),
    ]

    operations = [
        migrations.RunPython(add_beats,
                             reverse_code=migrations.RunPython.noop)
    ]
