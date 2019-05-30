# Generated by Django 2.1.4 on 2019-05-30 18:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('mail_collector', '0004_auto_20190530_1105'),
    ]

    operations = [
        migrations.AlterField(
            model_name='mailbotlogevent',
            name='source_host',
            field=models.ForeignKey(limit_choices_to={'excgh_last_seen__isnull': False}, on_delete=django.db.models.deletion.PROTECT, to='citrus_borg.WinlogbeatHost', verbose_name='Event Source Host'),
        ),
    ]
