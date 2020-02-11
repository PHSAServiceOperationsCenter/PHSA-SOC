# Generated by Django 2.2.6 on 2020-01-17 16:56
from django.conf import settings
from django.contrib.auth.models import User
from django.db import migrations
from django.utils import dateparse


def populate_event_sources(apps, schema_editor):
    model = apps.get_model('citrus_borg', 'AllowedEventSource')

    user = User.objects.filter(username=settings.CITRUS_BORG_SERVICE_USER)
    if user.exists():
        user = user.get()
    else:
        user = User.objects.create_user(settings.CITRUS_BORG_SERVICE_USER)

    event_source = model(source_name='ControlUp Logon Monitor')
    event_source.created_by_id = user.id
    event_source.updated_by_id = user.id

    event_source.save()


def delete_eventsources(apps, schema_editor):
    model = apps.get_model('citrus_borg', 'AllowedEventSource')

    model.objects.all().delete()


def populate_windows_logs(apps, schema_editor):
    model = apps.get_model('citrus_borg', 'WindowsLog')

    user = User.objects.filter(username=settings.CITRUS_BORG_SERVICE_USER)
    if user.exists():
        user = user.get()
    else:
        user = User.objects.create_user(settings.CITRUS_BORG_SERVICE_USER)

    winlog = model(log_name='Application')
    winlog.created_by_id = user.id
    winlog.updated_by_id = user.id

    winlog.save()


def delete_windowslogs(apps, schema_editor):
    model = apps.get_model('citrus_borg', 'WindowsLog')

    model.objects.all().delete()


def populate_sites(apps, schema_editor):
    sites_and_bots = [
        {'site': 'Squamish', 'notes': None,
         'bots': [{'host_name': 'bccss-t450s-02',
                   'ip_address': '10.42.208.35',
                   'fqdn': 'bccss-t450s-02.healthbc.org', },
                  {'host_name': 'bccss-t450s-04',
                   'ip_address': '10.21.179.4',
                   'fqdn': 'bccss-t450s-04.healthbc.org', }, ], },
        {'site': 'LGH', 'notes': "Lion's Gate Hospital",
         'bots': [{'host_name': 'bccss-t450s-07',
                   'ip_address': '139.173.100.206',
                   'fqdn': 'bccss-t450s-07.healthbc.org', },
                  {'host_name': 'bccss-t450s-10',
                   'ip_address': '10.21.201.93',
                   'fqdn': 'bccss-t450s-10.healthbc.org', }, ], },
        {'site': 'Whistler',  'notes': None,
         'bots': [{'host_name': 'LD023254',
                   'ip_address': '139.173.209.95',
                   'fqdn': 'LD023254.healthbc.org', },
                  {'host_name': 'LD023252',
                   'ip_address': '139.173.209.75',
                   'fqdn': 'LD023252.healthbc.org', }, ], },
        {'site': 'Pemberton',  'notes': None,
         'bots': [{'host_name': 'LD023258',
                   'ip_address': '139.173.207.153',
                   'fqdn': 'LD023258.healthbc.org', },
                  {'host_name': 'LD022367',
                   'ip_address': '139.173.207.133',
                   'fqdn': 'LD022367.healthbc.org', }, ], },
        {'site': 'Bella Bella',  'notes': None,
         'bots': [{'host_name': 'LD038073',
                   'ip_address': '139.173.203.178',
                   'fqdn': 'LD038073.healthbc.org', },
                  {'host_name': 'LD038074',
                   'ip_address': '139.173.203.159',
                   'fqdn': 'LD038074.healthbc.org', }, ], },
        {'site': 'Bella Coola',  'notes': None,
         'bots': [{'host_name': 'LD038075',
                   'ip_address': '10.21.175.98',
                   'fqdn': 'LD038075.healthbc.org', },
                  {'host_name': 'LD038076',
                   'ip_address': '10.21.175.184',
                   'fqdn': 'LD038076.healthbc.org', }, ], },
        {'site': 'Sechelt',  'notes': None,
         'bots': [{'host_name': 'LD021386',
                   'ip_address': '10.21.241.66',
                   'fqdn': 'LD021386.healthbc.org', }, ], },
        {'site': 'Powel River',  'notes': None,
         'bots': [{'host_name': 'LD030360',
                   'ip_address': '10.21.228.152',
                   'fqdn': 'LD030360.healthbc.org', }, ], },
    ]

    site_model = apps.get_model('citrus_borg', 'BorgSite')

    user = User.objects.filter(username=settings.CITRUS_BORG_SERVICE_USER)
    if user.exists():
        user = user.get()
    else:
        user = User.objects.create_user(settings.CITRUS_BORG_SERVICE_USER)

    for _site in sites_and_bots:
        site = site_model.objects.filter(site__iexact=_site['site'])

        if site.exists():
            site = site.get()
            site.notes = _site['notes']
        else:
            site = site_model(
                site=_site['site'], notes=_site['notes'],
                created_by_id=user.id, updated_by_id=user.id)

        site.save()


def populate_bots(apps, schema_editor):
    sites_and_bots = [
        {'site': 'Squamish', 'notes': None,
         'bots': [{'host_name': 'bccss-t450s-02',
                   'ip_address': '10.42.208.35',
                   'fqdn': 'bccss-t450s-02.healthbc.org', },
                  {'host_name': 'bccss-t450s-04',
                   'ip_address': '10.21.179.4',
                   'fqdn': 'bccss-t450s-04.healthbc.org', }, ], },
        {'site': 'LGH', 'notes': "Lion's Gate Hospital",
         'bots': [{'host_name': 'bccss-t450s-07',
                   'ip_address': '139.173.100.206',
                   'fqdn': 'bccss-t450s-07.healthbc.org', },
                  {'host_name': 'bccss-t450s-10',
                   'ip_address': '10.21.201.93',
                   'fqdn': 'bccss-t450s-10.healthbc.org', }, ], },
        {'site': 'Whistler',  'notes': None,
         'bots': [{'host_name': 'LD023254',
                   'ip_address': '139.173.209.95',
                   'fqdn': 'LD023254.healthbc.org', },
                  {'host_name': 'LD023252',
                   'ip_address': '139.173.209.75',
                   'fqdn': 'LD023252.healthbc.org', }, ], },
        {'site': 'Pemberton',  'notes': None,
         'bots': [{'host_name': 'LD023258',
                   'ip_address': '139.173.207.153',
                   'fqdn': 'LD023258.healthbc.org', },
                  {'host_name': 'LD022367',
                   'ip_address': '139.173.207.133',
                   'fqdn': 'LD022367.healthbc.org', }, ], },
        {'site': 'Bella Bella',  'notes': None,
         'bots': [{'host_name': 'LD038073',
                   'ip_address': '139.173.203.178',
                   'fqdn': 'LD038073.healthbc.org', },
                  {'host_name': 'LD038074',
                   'ip_address': '139.173.203.159',
                   'fqdn': 'LD038074.healthbc.org', }, ], },
        {'site': 'Bella Coola',  'notes': None,
         'bots': [{'host_name': 'LD038075',
                   'ip_address': '10.21.175.98',
                   'fqdn': 'LD038075.healthbc.org', },
                  {'host_name': 'LD038076',
                   'ip_address': '10.21.175.184',
                   'fqdn': 'LD038076.healthbc.org', }, ], },
        {'site': 'Sechelt',  'notes': None,
         'bots': [{'host_name': 'LD021386',
                   'ip_address': '10.21.241.66',
                   'fqdn': 'LD021386.healthbc.org', }, ], },
        {'site': 'Powel River',  'notes': None,
         'bots': [{'host_name': 'LD030360',
                   'ip_address': '10.21.228.152',
                   'fqdn': 'LD030360.healthbc.org', }, ], },
    ]

    site_model = apps.get_model('citrus_borg', 'BorgSite')
    borg_model = apps.get_model('citrus_borg', 'WinlogbeatHost')

    user = User.objects.filter(username=settings.CITRUS_BORG_SERVICE_USER)
    if user.exists():
        user = user.get()
    else:
        user = User.objects.create_user(settings.CITRUS_BORG_SERVICE_USER)

    for _site in sites_and_bots:
        site = site_model.objects.filter(site__iexact=_site['site']).get()
        for _bot in _site['bots']:
            bot = borg_model.objects.filter(host_name__iexact=_bot['host_name'])
            if bot.exists():
                bot = bot.get()
                bot.site = site
                bot.ip_address = _bot['ip_address']
            else:
                bot = borg_model(
                    host_name=_bot['host_name'], ip_address=_bot['ip_address'],
                    site=site,
                    last_seen=dateparse.parse_datetime(
                        '1970-01-01T00:00:00+00'),
                    created_by_id=user.id, updated_by_id=user.id)

            bot.save()


class Migration(migrations.Migration):
    replaces = [
        ('citrus_borg', '0003_populate_event_sources'),
        ('citrus_borg', '0004_populate_windows_logs'),
        ('citrus_borg', '0006_populate_sites'),
        ('citrus_borg', '0007_populate_bots'),



    ]

    dependencies = [
        ('citrus_borg', '0029_0001_to_0027_foreign_keys'),
        ('auth', '0011_update_proxy_permissions'),
    ]

    operations = [
        migrations.RunPython(populate_event_sources,
                             reverse_code=delete_eventsources),
        migrations.RunPython(populate_windows_logs,
                             reverse_code=delete_windowslogs),
        migrations.RunPython(populate_sites,
                             reverse_code=migrations.RunPython.noop),
        migrations.RunPython(populate_bots,
                             reverse_code=migrations.RunPython.noop)
    ]
