# Generated by Django 2.2.6 on 2019-11-13 18:50

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail_collector', '0040_add_subscription_unconfig_bots'),
    ]

    operations = [
        migrations.AlterField(
            model_name='exchangeconfiguration',
            name='backoff_factor',
            field=models.IntegerField(default=3, help_text='The Exchange client is using a `Retry Pattern With Exponential Back-off` mechanism when sending a message or when checking for a received message. This field contains the back-off factor used when retrying such and action', verbose_name='Back-off factor for retrying an Exchange action'),
        ),
        migrations.AlterField(
            model_name='exchangeconfiguration',
            name='max_wait_receive',
            field=models.DurationField(default=datetime.timedelta(0, 120), help_text='The Exchange client is using a `Retry Pattern With Exponential Back-off` mechanism when sending a message or when checking for a received message. This field contains the maximum time to wait before giving up on retrying such and action', verbose_name='Maximum time to wait before giving up on an Exchange action'),
        ),
        migrations.AlterField(
            model_name='exchangeconfiguration',
            name='min_wait_receive',
            field=models.DurationField(default=datetime.timedelta(0, 3), help_text='The Exchange client is using a `Retry Pattern With Exponential Back-off` mechanism when sending a message or when checking for a received message. This field contains the minimum wait time before retrying such and action', verbose_name='Minimum wait when retrying an Exchange action'),
        ),
    ]
