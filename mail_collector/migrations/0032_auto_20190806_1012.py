# Generated by Django 2.2.3 on 2019-08-06 17:12

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail_collector', '0031_auto_20190802_0935'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exchangeaccount',
            name='smtp_address',
            field=models.EmailField(db_index=True, help_text='Exchange Account', max_length=253, unique=True, verbose_name='SMTP address'),
        ),
        migrations.AlterField(
            model_name='exchangeconfiguration',
            name='max_wait_receive',
            field=models.DurationField(default=datetime.timedelta(0, 120), verbose_name='Timeout while checking for a a received message'),
        ),
        migrations.AlterField(
            model_name='witnessemail',
            name='smtp_address',
            field=models.EmailField(db_index=True, help_text='Exchange Account', max_length=253, unique=True, verbose_name='SMTP address'),
        ),
    ]
