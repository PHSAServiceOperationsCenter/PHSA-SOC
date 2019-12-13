# Generated by Django 2.2.6 on 2019-11-25 19:44

from django.db import migrations
import django.db.models.manager


class Migration(migrations.Migration):

    dependencies = [
        ('ldap_probe', '0012_auto_20191122_1537'),
    ]

    operations = [
        migrations.CreateModel(
            name='LdapProbeAnonBindLog',
            fields=[
            ],
            options={
                'verbose_name': 'AD service probe with limited data',
                'verbose_name_plural': 'AD service probes with limited data',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('ldap_probe.ldapprobelog',),
        ),
        migrations.CreateModel(
            name='LdapProbeFullBindLog',
            fields=[
            ],
            options={
                'verbose_name': 'AD service probe with full data',
                'verbose_name_plural': 'AD service probes with full data',
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('ldap_probe.ldapprobelog',),
            managers=[
                ('obejcts', django.db.models.manager.Manager()),
            ],
        ),
        migrations.AlterModelOptions(
            name='ldapprobelog',
            options={'ordering': ('-created_on',), 'verbose_name': 'AD service probe', 'verbose_name_plural': 'AD service probes'},
        ),
    ]
