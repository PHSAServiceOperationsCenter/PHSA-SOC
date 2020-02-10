# Generated by Django 2.2.6 on 2019-12-05 21:11
import pytz
from django.db import migrations


def add_beats(apps, schema_editor):
    timezone = pytz.timezone('America/Vancouver')

    periodic_tasks = [
        #         {'name': ('AD controller monitoring: bootstrap probes'),
        #          'task': 'ldap_probe.tasks.bootstrap_ad_probes',
        #          'args': '', 'kwargs': '',
        #          'interval': {'every': 5,
        #                       'period': 'minutes', }, },
    ]

    cron_tasks = [
        {'name': ('AD controller monitoring: perf alert summary report, full bind, orion'),
         'task': 'ldap_probe.tasks.dispatch_ldap_report',
         'args': '["ldap_probe.orionadnode", false, "alert"]',
         'kwargs': '',
         'crontab': {'minute': '37',
                     'hour': '*', 'day_of_week': '*', 'day_of_month': '*',
                     'month_of_year': '*', 'timezone': timezone, }, },
        {'name': ('AD controller monitoring: perf alert summary report, anon bind, orion'),
         'task': 'ldap_probe.tasks.dispatch_ldap_report',
         'args': '["ldap_probe.orionadnode", true, "alert"]',
         'kwargs': '',
         'crontab': {'minute': '39',
                     'hour': '*', 'day_of_week': '*', 'day_of_month': '*',
                     'month_of_year': '*', 'timezone': timezone, }, },
        {'name': ('AD controller monitoring: perf alert summary report, full bind, non orion'),
         'task': 'ldap_probe.tasks.dispatch_ldap_report',
         'args': '["ldap_probe.nonorionadnode", false, "alert"]',
         'kwargs': '',
         'crontab': {'minute': '41',
                     'hour': '*', 'day_of_week': '*', 'day_of_month': '*',
                     'month_of_year': '*', 'timezone': timezone, }, },
        {'name': ('AD controller monitoring: perf alert summary report, anon bind, non orion'),
         'task': 'ldap_probe.tasks.dispatch_ldap_report',
         'args': '["ldap_probe.nonorionadnode", true, "alert"]',
         'kwargs': '',
         'crontab': {'minute': '43',
                     'hour': '*', 'day_of_week': '*', 'day_of_month': '*',
                     'month_of_year': '*', 'timezone': timezone, }, },
        {'name': ('AD controller monitoring: perf warning summary report, full bind, orion'),
         'task': 'ldap_probe.tasks.dispatch_ldap_report',
                 'args': '["ldap_probe.orionadnode", false, "warning"]',
                 'kwargs': '',
                 'crontab': {'minute': '45',
                             'hour': '*', 'day_of_week': '*', 'day_of_month': '*',
                             'month_of_year': '*', 'timezone': timezone, }, },
        {'name': ('AD controller monitoring: perf warning summary report, anon bind, orion'),
         'task': 'ldap_probe.tasks.dispatch_ldap_report',
         'args': '["ldap_probe.orionadnode", true, "warning"]',
         'kwargs': '',
         'crontab': {'minute': '47',
                     'hour': '*', 'day_of_week': '*', 'day_of_month': '*',
                     'month_of_year': '*', 'timezone': timezone, }, },
        {'name': ('AD controller monitoring: perf warning summary report, full bind, non orion'),
         'task': 'ldap_probe.tasks.dispatch_ldap_report',
         'args': '["ldap_probe.nonorionadnode", false, "warning"]',
         'kwargs': '',
         'crontab': {'minute': '49',
                     'hour': '*', 'day_of_week': '*', 'day_of_month': '*',
                     'month_of_year': '*', 'timezone': timezone, }, },
        {'name': ('AD controller monitoring: perf warning summary report, anon bind, non orion'),
         'task': 'ldap_probe.tasks.dispatch_ldap_report',
         'args': '["ldap_probe.nonorionadnode", true, "warning"]',
         'kwargs': '',
         'crontab': {'minute': '51',
                     'hour': '*', 'day_of_week': '*', 'day_of_month': '*',
                     'month_of_year': '*', 'timezone': timezone, }, },

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
        ('ldap_probe', '0024_beats_for_summary_reports'),
    ]

    operations = [
        migrations.RunPython(
            add_beats, reverse_code=migrations.RunPython.noop),
    ]
