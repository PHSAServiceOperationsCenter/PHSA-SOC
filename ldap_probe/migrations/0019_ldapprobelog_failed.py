# Generated by Django 2.2.6 on 2019-11-27 17:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ldap_probe', '0017_auto_20191126_1425'),
    ]

    operations = [
        migrations.AddField(
            model_name='ldapprobelog',
            name='failed',
            field=models.BooleanField(db_index=True, default=False, verbose_name='Probe failed'),
        ),
    ]
