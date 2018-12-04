# Generated by Django 2.1.1 on 2018-11-27 19:19

from django.db import migrations
from django.conf import settings
from django.contrib.auth.models import User


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

    Site = apps.get_model('citrus_borg', 'BorgSite')

    user = User.objects.filter(username=settings.CITRUS_BORG_SERVICE_USER)
    if user.exists():
        user = user.get()
    else:
        user = User.objects.create_user(settings.CITRUS_BORG_SERVICE_USER)

    for _site in sites_and_bots:
        site = Site.objects.filter(site__iexact=_site['site'])

        if site.exists():
            site = site.get()
            site.notes = _site['notes']
        else:
            site = Site(
                site=_site['site'], notes=_site['notes'],
                created_by_id=user.id, updated_by_id=user.id)

        site.save()


class Migration(migrations.Migration):

    dependencies = [
        ('citrus_borg', '0005_auto_20181126_1422'),
    ]

    operations = [
        migrations.RunPython(
            populate_sites, reverse_code=migrations.RunPython.noop)
    ]
