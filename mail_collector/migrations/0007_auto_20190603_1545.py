# Generated by Django 2.1.4 on 2019-06-03 22:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('mail_collector', '0006_auto_20190603_1059'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='mailbotlogevent',
            options={'get_latest_by': '-event_registered_on', 'ordering': ['-event_group_id', '-event_type'], 'verbose_name': 'Mail Monitoring Event', 'verbose_name_plural': 'Mail Monitoring Events'},
        ),
        migrations.AlterModelOptions(
            name='mailbotmessage',
            options={'get_latest_by': '-event__event_registered_on', 'ordering': ['-event__event_group_id', 'mail_message_identifier', '-event__event_type'], 'verbose_name': 'Mail Monitoring Message', 'verbose_name_plural': 'Mail Monitoring Messages'},
        ),
    ]