# Generated by Django 2.1.4 on 2019-04-04 17:45
import pytz

from django.contrib.auth.models import User

from django.db import migrations


def add_ssl_ports(apps, schema_editor):
    su = User.objects.filter(is_superuser=True).first()

    ports = [
        {'port': 261, 'enabled': False, 'notes': 'Nsiiops', },
        {'port': 443, 'enabled': True, 'notes': 'HTTPS', },
        {'port': 446, 'enabled': False,
         'notes': 'Openfiler management interface', },
        {'port': 448, 'enabled': False, 'notes': 'ddm-ssl', },
        {'port': 465, 'enabled': False, 'notes': 'SMTPS', },
        {'port': 563, 'enabled': False, 'notes': 'NNTPS', },
        {'port': 585, 'enabled': False, 'notes': 'imap4-ssl', },
        {'port': 614, 'enabled': False, 'notes': 'SSLshell', },
        {'port': 636, 'enabled': False, 'notes': 'LDAPS', },
        {'port': 684, 'enabled': False, 'notes': 'Corba IIOP SSL', },
        {'port': 695, 'enabled': False, 'notes': 'IEEE-MMS-SSL', },
        {'port': 902, 'enabled': False, 'notes': 'VMWare Auth Daemon', },
        {'port': 989, 'enabled': False, 'notes': 'FTPS data', },
    ]

    port_model = apps.get_model('ssl_cert_tracker', 'SslProbePort')

    for port_dict in ports:
        port_dict.update({'created_by_id': su.id, 'updated_by_id': su.id})
        port_model.objects.get_or_create(**port_dict)


class Migration(migrations.Migration):
    replaces = [
        ('ssl_cert_tracker', '0002_old_data_migrations'),
        ('ssl_cert_tracker', '0003_remove_getnmapdata'),
        ('ssl_cert_tracker', '0008_adjust_subscription_emails')
    ]

    dependencies = [
        ('ssl_cert_tracker', '0009_0001_to_0007_model'),
        ('auth', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_ssl_ports,
                             reverse_code=migrations.RunPython.noop),
    ]
