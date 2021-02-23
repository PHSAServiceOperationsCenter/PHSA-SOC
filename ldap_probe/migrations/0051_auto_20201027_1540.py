# Generated by Django 2.2.6 on 2020-10-27 22:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('ldap_probe', '0050_auto_20201022_1522'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='ldapprobelog',
            options={'get_latest_by': 'created', 'ordering': ('-created',), 'verbose_name': 'AD service probe', 'verbose_name_plural': 'AD service probes'},
        ),
        migrations.RenameField(
            model_name='adnodeperfbucket',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='ldapbindcred',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='ldapcrederror',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='ldapprobelog',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='nonorionadnode',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='orionadnode',
            old_name='created_on',
            new_name='created',
        ),
    ]
