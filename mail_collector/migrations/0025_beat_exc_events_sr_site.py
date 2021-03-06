# Generated by Django 2.1.4 on 2019-07-05 22:18
import pytz
from django.db import migrations


def add_beats(apps, schema_editor):
    timezone = pytz.timezone('America/Vancouver')

    periodic_tasks = []

    cron_tasks = [
        {
            'name': ('Exchange send receive by site report'),
            'task': 'mail_collector.tasks.invoke_report_events_by_site',
            'args': '',
            'kwargs': '',
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
        ('mail_collector', '0023_more_beats'),
    ]

    operations = [
        migrations.RunPython(add_beats,
                             reverse_code=migrations.RunPython.noop)
    ]
