import pytz
from django.apps import apps as django_apps
from django.db import migrations


# TODO put this into some sort of utils module?
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


def migrate_tasks(cron=(), interval=()):
    return migrations.RunPython(
        add_beats(cron, interval),
        reverse_code=remove_beats(cron + interval)
    )

CRON_TASKS = {
    'citrus_borg': [
        ({'name': 'Email Citrix Bot Report for Excessive Logon Response Time'
                  ' Events',
          'task': 'citrus_borg.tasks.email_failed_ux_report', },
         {'hour': '07,19', 'minute': '00'}, ),
        ({'name': 'Email Citrix Failed Logons Report',
          'task': 'citrus_borg.tasks.email_failed_logins_report', },
         {'hour': '06,18', 'minute': '30', }, ),
        ({'name': 'Trigger Emails with Citrix Failed Logons per Site Report',
          'task': 'citrus_borg.tasks.email_failed_login_sites_report', },
         {'hour': '06,18', 'minute': '35', }, ),
        ({'name': 'Purge windows logs events',
          'task': 'citrus_borg.tasks.expire_events', },
         {'minute': '01', 'hour': '01', }, ),
        ({'name': 'Dead Citrix monitoring bots report',
          'task': 'citrus_borg.tasks.email_dead_borgs_report', },
         {'minute': '00', 'hour': '07,19', }, ),
        ({'name': 'Dead Citrix client sites report',
          'task': 'citrus_borg.tasks.email_dead_sites_report', },
         {'minute': '00', 'hour': '07,19', }, ),
        ({'name': 'Dead Citrix farm hosts report',
          'task': 'citrus_borg.tasks.email_dead_servers_report', },
         {'minute': '00', 'hour': '07,19', }, ),
        ({'name': 'Citrix logon event summary',
          'task': 'citrus_borg.tasks.email_borg_login_summary_report', },
         {'minute': '00', 'hour': '07,19', }, ),
    ],

    'orion_flash': [
        ({'name': 'Refresh Orion alerts for dead Citrix bots',
          'task': 'orion_flash.tasks.refresh_borg_alerts',
          'args': '["orion_flash.deadcitrusbotalert"]', },
         {'minute': '21', 'hour': '07,15,23', }, ),
        ({'name': 'Refresh Orion alerts for untrusted SSL certificates',
          'task': 'orion_flash.tasks.refresh_ssl_alerts',
          'args': '["orion_flash.untrustedsslalert"]', },
         {'minute': '01', 'hour': '07,15,23', }, ),
        ({'name': 'Refresh Orion alerts for SSL certificates that will expire'
                  ' in less than 90 days',
          'task': 'orion_flash.tasks.refresh_ssl_alerts',
          'args': '["orion_flash.expiressoonsslalert"]',
          'kwargs': '{"lt_days":90}', },
         {'minute': '01', 'hour': '07,15,23', }, ),
        ({'name': 'Refresh Orion alerts for SSL certificates that will expire'
                  ' in less than 30 days',
          'task': 'orion_flash.tasks.refresh_ssl_alerts',
          'args': '["orion_flash.expiressoonsslalert"]',
          'kwargs': '{"lt_days":30}', },
         {'minute': '02', 'hour': '07,15,23', }, ),
        ({'name': 'Refresh Orion alerts for SSL certificates that will expire'
                  ' in less than 7 days',
          'task': 'orion_flash.tasks.refresh_ssl_alerts',
          'args': '["orion_flash.expiressoonsslalert"]',
          'kwargs': '{"lt_days":7}', },
         {'minute': '03', 'hour': '07,15,23', }, ),
        ({'name': 'Refresh Orion alerts for SSL certificates that will expire'
                  ' in less than 2 days',
          'task': 'orion_flash.tasks.refresh_ssl_alerts',
          'args': '["orion_flash.expiressoonsslalert"]',
          'kwargs': '{"lt_days":2}', },
         {'minute': '04', 'hour': '07,15,23', }, ),
        ({'name': 'Refresh Orion alerts for SSL certificates that have expired',
          'task': 'orion_flash.tasks.refresh_ssl_alerts',
          'args': '["orion_flash.expiredsslalert"]', },
         {'minute': '05', 'hour': '07,15,23', }, ),
        ({'name': 'Refresh Orion alerts for SSL certificates that are not yet'
                  ' valid',
          'task': 'orion_flash.tasks.refresh_ssl_alerts',
          'args': '["orion_flash.invalidsslalert"]',
          'kwargs': '{}', },
         {'minute': '06', 'hour': '07,15,23', }, ),
        ({'name': 'Purge Orion alerts for SSL certificates',
          'task': 'orion_flash.tasks.purge_ssl_alerts', },
         {'minute': '55', 'hour': '06,14,22', }, ),
    ],

    'ldap_probe': [
        ({'name': 'AD controller monitoring: expire log entries',
          'task': 'ldap_probe.tasks.expire_entries', },
         {'minute': '11', 'hour': '00', }, ),
        ({'name': 'AD controller monitoring: delete expired log entries',
          'task': 'ldap_probe.tasks.delete_expire_entries', },
         {'minute': '17', 'hour': '00', }, ),
        ({'name': 'AD controller monitoring: remove duplicate AD nodes',
          'task': 'ldap_probe.tasks.trim_ad_duplicates', },
         {'minute': '11', 'hour': '09', }, ),
        ({'name': 'AD controller monitoring: summary report, full bind, orion',
          'task': 'ldap_probe.tasks.dispatch_ldap_report',
          'args': '["ldap_probe.orionadnode", false, null]', },
         {'minute': '29', 'hour': '*', }, ),
        ({'name': 'AD controller monitoring: summary report, anon bind, orion',
          'task': 'ldap_probe.tasks.dispatch_ldap_report',
          'args': '["ldap_probe.orionadnode", true, null]', },
         {'minute': '31', 'hour': '*', }, ),
        ({'name': 'AD controller monitoring: summary report, full bind, non '
                  'orion',
          'task': 'ldap_probe.tasks.dispatch_ldap_report',
          'args': '["ldap_probe.nonorionadnode", false, null]', },
         {'minute': '33', 'hour': '*', }, ),
        ({'name': 'AD controller monitoring: summary report, anon bind, non '
                  'orion',
          'task': 'ldap_probe.tasks.dispatch_ldap_report',
          'args': '["ldap_probe.nonorionadnode", true, null]', },
         {'minute': '35', 'hour': '*', }, ),
        ({'name': 'AD controller monitoring: error summary report',
          'task': 'ldap_probe.tasks.dispatch_ldap_error_report', },
         {'minute': '53', 'hour': '*', }, ),
        ({'name': 'AD controller monitoring: non Orion AD nodes report',
          'task': 'ldap_probe.tasks.dispatch_non_orion_ad_nodes_report', },
         {'minute': '53', 'hour': '06', }, ),
        ({'name': 'AD controller monitoring: FQDN Orion AD nodes report',
          'task': 'ldap_probe.tasks.dispatch_bad_fqdn_reports', },
         {'minute': '54', 'hour': '06', }, ),
        ({'name': 'AD controller monitoring: Duplicate Orion AD nodes report',
          'task': 'ldap_probe.tasks.dispatch_dupe_nodes_reports', },
         {'minute': '57', 'hour': '06', }, ),
        ({'name': 'AD controller monitoring: maintain Orion AD nodes',
          'task': 'ldap_probe.tasks.maintain_ad_orion_nodes', },
         {'minute': '23', 'hour': '08', }, ),
        ({'name': 'AD controller monitoring: performance degradation reports',
          'task': 'ldap_probe.tasks.dispatch_ldap_perf_reports', },
         {'minute': '37', 'hour': '*', }, ),
    ],

    'mail_collector': [
        ({'name': 'Dead exchange servers report',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_updated__lte",'
                  '"Exchange Servers Not Seen"]',
          'kwargs': '{"url_annotate": true,'
                    '"level": null,'
                    '"filter_pref": "exchange__report_interval",'
                    '"to_orion": false, "enabled": true}', },
         {'minute': '45', 'hour': '07,15,23', }, ),
        ({'name': 'No connect exchange servers report',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_connection__lte",'
                  '"Exchange Servers No Connection"]',
          'kwargs': '{"url_annotate": true,'
                    '"level": null,'
                    '"filter_pref": "exchange__report_interval",'
                    '"enabled": true}', },
         {'minute': '45', 'hour': '07,15,23', }, ),
        ({'name': 'No send exchange servers report',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_send__lte",'
                  '"Exchange Servers No Send"]',
          'kwargs': '{"url_annotate": true,'
                    '"level": null,'
                    '"filter_pref": "exchange__report_interval",'
                    '"enabled": true}', },
         {'minute': '45', 'hour': '07,15,23', }, ),
        ({'name': 'No receive exchange servers report',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_inbox_access__lte",'
                  '"Exchange Servers No Receive"]',
          'kwargs': '{"url_annotate": true,'
                    '"level": null,'
                    '"filter_pref": "exchange__report_interval",'
                    '"enabled": true}', },
         {'minute': '45', 'hour': '07,15,23', }, ),
        ({'name': 'Dead exchange databases report',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangedatabase","last_access__lte",'
                  '"Exchange Databases Not Seen"]',
          'kwargs': '{"url_annotate": true,'
                    '"level": null,'
                    '"filter_pref": "exchange__report_interval",'
                    '"enabled": true}', },
         {'minute': '45', 'hour': '07,15,23', }, ),
        ({'name': 'Exchange verification report',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.mailbetweendomains","last_verified__gte",'
                  '"Mail Unchecked On Site"]',
          'kwargs': '{"url_annotate": true,'
                    '"level": null,'
                    '"filter_pref": "exchange__report_interval",'
                    '"enabled": true,'
                    '"is_expired": false}', },
         {'minute': '45', 'hour': '07,15,23', }, ),
        ({'name': 'Exchange send receive by site report',
          'task': 'mail_collector.tasks.invoke_report_events_by_site', },
         {'minute': '45', 'hour': '07,15,23', }, ),
        ({'name': 'Exchange send receive by bot report',
          'task': 'mail_collector.tasks.invoke_report_events_by_bot', },
         {'minute': '45', 'hour': '07,15,23', }, ),
    ],

    'ssl_cert': [
        ({'name': 'Bootstrap nmap probes to collect SSL certificates',
          'task': 'ssl_cert_tracker.tasks.get_ssl_nodes', },
         {'hour': '06,18', 'minute': '08', }, ),
        ({'name': 'Bootstrap nmap probes to verify SSL certificates',
          'task': 'ssl_cert_tracker.tasks.verify_ssl_certificates', },
         {'hour': '02', 'minute': '35', }, ),
    ],
}

INTERVAL_TASKS = {
    'citrus_borg': [
        ({'name': 'Refresh Orion node ID values for Citrix bots',
          'task': 'citrus_borg.tasks.get_orion_ids', },
         {'every': 24, 'period': 'hours', }, ),
        ({'name': 'Dead Citrix monitoring bots alert',
          'task': 'citrus_borg.tasks.email_dead_borgs_alert'},
         {'every': 10, 'period': 'minutes', }),
        ({'name': 'Dead Citrix client sites alert',
          'task': 'citrus_borg.tasks.email_dead_sites_alert', },
         {'every':  10, 'period': 'minutes', },),
        ({'name': 'Dead Citrix farm hosts alert',
          'task': 'citrus_borg.tasks.email_dead_servers_alert'},
         {'every':  12, 'period': 'hours', }, ),
        ({'name': 'Citrix failed logon alerts',
          'task': 'citrus_borg.tasks.email_failed_login_alarm', },
         {'every':  10, 'period': 'minutes', }, ),
    ],

    'orion_flash': [
        ({'name': 'Refresh Orion alerts for Citrix logons',
          'task': 'orion_flash.tasks.refresh_borg_alerts',
          'args': '["orion_flash.citrusborgloginalert"]', },
         {'every': 12, 'period': 'minutes', },),
        ({'name': 'Refresh Orion alerts for Citrix response times',
          'task': 'orion_flash.tasks.refresh_borg_alerts',
          'args': '["orion_flash.citrusborguxalert"]', },
         {'every': 12, 'period': 'minutes', }, ),
    ],

    'ldap_probe': [
        ({'name': 'AD controller monitoring: bootstrap probes',
          'task': 'ldap_probe.tasks.bootstrap_ad_probes', },
         {'every': 5, 'period': 'minutes', }, ),
    ],

    'mail_collector': [
        ({'name': 'Raise warning alert for exchange servers',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_updated__lte",'
                  '"Exchange Servers Not Seen"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "WARNING",'
                    '"filter_pref": "exchange__server_warn",'
                    '"to_orion": false, "enabled": true}', },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise critical  alert for exchange servers',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_updated__lte",'
                  '"Exchange Servers Not Seen"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "CRITICAL",'
                    '"filter_pref": "exchange__server_error","enabled": true}',
          },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise critical  alert for connections to exchange servers',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_connection__lte",'
                  '"Exchange Servers No Connection"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "CRITICAL",'
                    '"filter_pref": "exchange__server_error","enabled": true}',
          },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise warning  alert for connections to exchange servers',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_connection__lte",'
                  '"Exchange Servers No Connection"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "WARNING",'
                    '"filter_pref": "exchange__server_warn","enabled": true}',
          },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise critical  alert for send to exchange servers',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_send__lte",'
                  '"Exchange Servers No Send"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "CRITICAL",'
                    '"filter_pref": "exchange__server_error","enabled": true}',
          },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise warning  alert for send to exchange servers',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_send__lte",'
                  '"Exchange Servers No Send"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "WARNING",'
                    '"filter_pref": "exchange__server_warn","enabled": true}',
          },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise critical  alert for receive to exchange servers',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_inbox_access__lte",'
                  '"Exchange Servers No Receive"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "CRITICAL",'
                    '"filter_pref": "exchange__server_error","enabled": true}',
          },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise warning  alert for receive to exchange servers',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangeserver","last_inbox_access__lte",'
                  '"Exchange Servers No Receive"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "WARNING",'
                    '"filter_pref": "exchange__server_warn","enabled": true}',
          },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise critical  alert for exchange databases',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangedatabase","last_access__lte",'
                  '"Exchange Databases Not Seen"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "CRITICAL",'
                    '"filter_pref": "exchange__server_error","enabled": true}',
          },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise warning  alert for exchange databases',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.exchangedatabase","last_access__lte",'
                  '"Exchange Databases Not Seen"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "WARNING",'
                    '"filter_pref": "exchange__server_warn","enabled": true}',
          },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise critical  alert for exchange client bots',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.mailhost","excgh_last_seen__lte",'
                  '"Exchange Client Bots Not Seen"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "CRITICAL",'
                    '"filter_pref": "exchange__bot_error","enabled": true}', },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise warning  alert for exchange client bots',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.mailhost","excgh_last_seen__lte",'
                  '"Exchange Client Bots Not Seen"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "WARNING",'
                    '"filter_pref": "exchange__bot_warn","enabled": true}', },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise warning  alert for exchange client sites',
          'task': 'mail_collector.tasks.dead_mail_sites',
          'args': '["Exchange Client Bot Sites Not Seen"]',
          'kwargs': '{"level": "WARNING",'
                    '"time_delta_pref": "exchange__bot_warn"}', },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise critical  alert for exchange client sites',
          'task': 'mail_collector.tasks.dead_mail_sites',
          'args': '["Exchange Client Bot Sites Not Seen"]',
          'kwargs': '{"level": "CRITICAL",'
                    '"time_delta_pref": "exchange__bot_error"}', },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise critical  alert for email not checked',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.mailbetweendomains","last_verified__lte",'
                  '"Mail Unchecked On Site"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "CRITICAL",'
                    '"filter_pref": "exchange__bot_error",'
                    '"enabled": true, '
                    '"is_expired": false}', },
         {'every': 30, 'period': 'minutes', }, ),
        ({'name': 'Raise critical  alert for email check failure',
          'task': 'mail_collector.tasks.bring_out_your_dead',
          'args': '["mail_collector.mailbetweendomains","last_verified__lte",'
                  '"Mail Verification Failed"]',
          'kwargs': '{"url_annotate": false,'
                    '"level": "CRITICAL",'
                    '"filter_pref": "exchange__nil_duration",'
                    '"enabled": true,'
                    '"is_expired": false,'
                    '"status": "Failed"}', },
         {'every': 30, 'period': 'minutes', }, ),
    ],

    'ssl_cert': [

    ]
}


class Migration(migrations.Migration):
    replaces = [
        ('citrus_borg', '0009_prepare_task_scheddules'),
        ('citrus_borg', '0014_add_failed_login_tasks'),
        ('citrus_borg', '0018_add_periodic_tasks'),
        ('citrus_borg', '0019_disable_beats_for_email_alerts'),
        ('citrus_borg', '0020_change_beat_to_07_19'),
        ('citrus_borg', '0021_update_more_beats_to_07_19'),
        ('citrus_borg', '0022_fix_beats_for_reports'),
        ('ldap_probe', '0010_add_beats_for_ldap_data'),
        ('ldap_probe', '0015_realy_add_beats_for_ldap_data'),
        ('ldap_probe', '0018_add_beat_for_removing_non_orion_nodes'),
        ('ldap_probe', '0024_beats_for_summary_reports'),
        ('ldap_probe', '0026_beats_for_perf_summary_reports'),
        ('ldap_probe', '0028_err_reports_beats'),
        ('ldap_probe', '0030_nono_adnodes_rep_beats'),
        ('ldap_probe', '0032_orion_adnodes_rep_beats'),
        ('ldap_probe', '0034_perf_bucket_generic'),
        ('ldap_probe', '0038_maintain_nodes_beat'),
        ('ldap_probe', '0039_del_beats_old_perf_reports'),
        ('ldap_probe', '0040_beats_new_perf_reports'),
        ('mail_collector', '0018_add_beats_for_dead_bodies'),
        ('mail_collector', '0020_more_beats_for_dead_bodies'),
        ('mail_collector', '0023_more_beats'),
        ('mail_collector', '0025_beat_exc_events_sr_site'),
        ('mail_collector', '0027_beat_exc_evnts_site'),
        ('orion_integration', '0010_remove_heart_beat_task'),
    ]

    dependencies = [
        ('django_celery_beat', '0011_auto_20190508_0153'),
    ]

    operations = [
        migrate_tasks(
            CRON_TASKS.get(app_name, []),
            INTERVAL_TASKS.get(app_name, [])
        )
        for app_name in [app.name for app in django_apps.get_app_configs()]
    ]
