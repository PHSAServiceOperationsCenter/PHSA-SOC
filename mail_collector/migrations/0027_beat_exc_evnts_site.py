# Generated by Django 2.1.4 on 2019-07-08 20:58
import pytz

from django.db import migrations


def add_beats(apps, schema_editor):
    timezone = pytz.timezone('America/Vancouver')

    periodic_tasks = [
        #         {
        #             'name': ('Raise critical  alert for exchange client bots'),
        #             'task': 'mail_collector.tasks.bring_out_your_dead',
        #             'args': (
        #                 '["mail_collector.mailhost","excgh_last_seen__lte",'
        #                 '"Exchange Client Bots Not Seen"]'),
        #             'kwargs': (
        #                 '{"url_annotate": false,'
        #                 '"level": "CRITICAL",'
        #                 '"filter_pref": "exchange__bot_error","enabled": true}'),
        #             'interval': {
        #                 'every': 30,
        #                 'period': 'minutes',
        #             },
        #         },
    ]

    cron_tasks = [


        {
            'name': ('Exchange send receive by bot report'),
            'task': 'mail_collector.tasks.invoke_report_events_by_bot',
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
        ('mail_collector', '0026_subscription_exc_evts_bot'),
    ]

    operations = [
        migrations.RunPython(add_beats,
                             reverse_code=migrations.RunPython.noop)
    ]
