# Generated by Django 2.2.6 on 2019-11-25 22:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ldap_probe', '0013_auto_20191125_1144'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='orionadnode',
            options={'ordering': ('node__node_caption',), 'verbose_name': 'Domain Controller from Orion', 'verbose_name_plural': 'Domain Controllers from Orion'},
        ),
    ]