# Generated by Django 2.1.1 on 2018-11-16 17:01

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ssl_cert_tracker', '0009_report_tasks_cronjobs'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subscription',
            name='from_email',
            field=models.CharField(blank=True, default=['serban.teodorescu@phsa.ca'], max_length=255, null=True, verbose_name='from'),
        ),
    ]