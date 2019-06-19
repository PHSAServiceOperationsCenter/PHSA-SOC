# Generated by Django 2.1.4 on 2019-06-19 17:37
import pytz
from django.db import migrations


def add_beats(apps, schema_editor):
    timezone = pytz.timezone('America/Vancouver')

    periodic_tasks = [
        {
            'name': ('Raise warning alert for exchange servers'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_updated__lte",'
                '"Exchange Servers Not Seen"]'),
            'kwargs': (
                '{"url_annotate": false,'
                '"level": "WARNING",'
                '"filter_pref": "exchange__server_warn",'
                '"by_mail": true, "to_orion": false, "enabled": true}'),
            'interval': {
                'every': 30,
                'period': 'minutes',
            },
        },

    ]

    cron_tasks = [
        {
            'name': ('Dead exchange servers report'),
            'task': 'mail_collector.tasks.bring_out_your_dead',
            'args': (
                '["mail_collector.exchangeserver","last_updated__lte",'
                '"Exchange Servers Not Seen"]'),
            'kwargs': (
                '{"url_annotate": true,'
                '"level": null,'
                '"filter_pref": "exchange__report_interval",'
                '"by_mail": true, "to_orion": false, "enabled": true}'),
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
        ('mail_collector', '0017_add_mail_function_subscriptions'),
    ]

    operations = [
        migrations.RunPython(add_beats,
                             reverse_code=migrations.RunPython.noop)
    ]
