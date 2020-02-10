# Generated by Django 2.2.6 on 2019-12-17 22:35

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import ldap_probe.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('ldap_probe', '0021_ldapprobelogfailed'),
    ]

    operations = [
        migrations.AlterField(
            model_name='nonorionadnode',
            name='node_dns',
            field=models.CharField(db_index=True, help_text='The FQDN of the domain controller host. It must respect the rules specified in `RFC1123 <http://www.faqs.org/rfcs/rfc1123.html>`__, section 2.1', max_length=255, unique=True, verbose_name='Fully Qualified Domain Name (FQDN)'),
        ),
        migrations.CreateModel(
            name='ADNodePerfBucket',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_on', models.DateTimeField(auto_now_add=True, db_index=True, help_text='object creation time stamp', verbose_name='created on')),
                ('updated_on', models.DateTimeField(auto_now=True, db_index=True, help_text='object update time stamp', verbose_name='updated on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is checked out, the row will always be excluded from any active operation', verbose_name='enabled')),
                ('notes', models.TextField(blank=True, null=True, verbose_name='notes')),
                ('is_default', models.BooleanField(db_index=True, default=False, verbose_name='default windows account')),
                ('location', models.CharField(db_index=True, help_text='Information pertaining to the geographical area to which a group of performance degradation limits applies', max_length=253, unique=True, verbose_name='Location Key')),
                ('avg_warn_threshold', models.DecimalField(db_index=True, decimal_places=3, help_text='If the average AD services response time is worse than this value, include this node in the periodic performance degradation warnings report.', max_digits=4, verbose_name='Warning Response Time Threshold')),
                ('avg_err_threshold', models.DecimalField(db_index=True, decimal_places=3, help_text='If the average AD services response time is worse than this value, include this node in the periodic performance degradation errors report.', max_digits=4, verbose_name='Error Response Time Threshold')),
                ('alert_threshold', models.DecimalField(db_index=True, decimal_places=3, help_text='If the AD services response time for any probe is worse than this value, raise an immediate alert.', max_digits=4, verbose_name='Alert Response Time Threshold')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ldap_probe_adnodeperfbucket_created_by_related', to=settings.AUTH_USER_MODEL, verbose_name='created by')),
                ('updated_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='ldap_probe_adnodeperfbucket_updated_by_related', to=settings.AUTH_USER_MODEL, verbose_name='updated by')),
            ],
            options={
                'verbose_name': 'Performance Group for ADS Nodes',
                'verbose_name_plural': 'Performance Groups for ADS Nodes',
            },
        ),
        migrations.AddField(
            model_name='nonorionadnode',
            name='location',
            field=models.ForeignKey(blank=True, default=ldap_probe.models.ADNodePerfBucket.get_default, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='ldap_probe.ADNodePerfBucket', verbose_name='Acceptable Performance Limits'),
        ),
        migrations.AddField(
            model_name='orionadnode',
            name='location',
            field=models.ForeignKey(blank=True, default=ldap_probe.models.ADNodePerfBucket.get_default, null=True, on_delete=django.db.models.deletion.SET_DEFAULT, to='ldap_probe.ADNodePerfBucket', verbose_name='Acceptable Performance Limits'),
        ),
    ]
