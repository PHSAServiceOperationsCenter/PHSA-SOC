# Generated by Django 2.2.6 on 2020-10-22 22:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ldap_probe', '0049_auto_20200420_0928'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ldapprobelog',
            options={'get_latest_by': 'created_on', 'ordering': ('-created_on',), 'verbose_name': 'AD service probe', 'verbose_name_plural': 'AD service probes'},
        ),
    ]
