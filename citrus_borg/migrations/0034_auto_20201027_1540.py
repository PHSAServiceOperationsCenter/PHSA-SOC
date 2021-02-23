# Generated by Django 2.2.6 on 2020-10-27 22:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('citrus_borg', '0033_auto_20200724_1136'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='winlogevent',
            options={'get_latest_by': 'created', 'ordering': ['-created'], 'verbose_name': 'Citrix Bot Windows Log Event', 'verbose_name_plural': 'Citrix Bot Windows Log Events'},
        ),
        migrations.RenameField(
            model_name='allowedeventsource',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='borgsite',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='eventcluster',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='knownbrokeringdevice',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='windowslog',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='winlogbeathost',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='winlogevent',
            old_name='created_on',
            new_name='created',
        ),
    ]
