# Generated by Django 2.2.6 on 2020-01-23 22:57

from django.db import migrations, models
import django.db.models.deletion
import ldap_probe.models


class Migration(migrations.Migration):

    dependencies = [
        ('ldap_probe', '0046_merge_20200121_1538'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nonorionadnode',
            name='performance_bucket',
            field=models.ForeignKey(default=ldap_probe.models.ADNodePerfBucket.get_default, on_delete=django.db.models.deletion.SET_DEFAULT, to='ldap_probe.ADNodePerfBucket', verbose_name='Acceptable Performance Limits'),
        ),
        migrations.AlterField(
            model_name='orionadnode',
            name='performance_bucket',
            field=models.ForeignKey(default=ldap_probe.models.ADNodePerfBucket.get_default, on_delete=django.db.models.deletion.SET_DEFAULT, to='ldap_probe.ADNodePerfBucket', verbose_name='Acceptable Performance Limits'),
        ),
    ]