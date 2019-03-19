# Generated by Django 2.1.4 on 2019-01-29 18:36

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SslInvalidAuxAlert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orion_node_id', models.BigIntegerField(db_index=True, help_text='this is the value in this field to SQL join the Orion server database', verbose_name='Orion Node Id')),
                ('ssl_cert_url', models.URLField(verbose_name='SSL certificate URL')),
                ('ssl_cert_subject', models.TextField(verbose_name='SSL certificate subject')),
                ('raised_on', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='alert raised on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is disabled, the Orion alert will not be raised', verbose_name='alert enabled')),
                ('self_url', models.URLField(blank=True, null=True, verbose_name='SSL certificate URL')),
                ('ssl_alert_body', models.TextField(verbose_name='alert body')),
                ('ssl_cert_issuer', models.TextField(verbose_name='SSL certificate issuing authority')),
                ('not_before', models.DateTimeField(db_index=True, verbose_name='not valid before')),
                ('not_after', models.DateTimeField(db_index=True, verbose_name='expires on')),
            ],
            options={
                'verbose_name': 'Custom Orion Alert for SSL certificates Validity',
                'verbose_name_plural': 'Custom Orion Alerts for SSL certificates Validity',
            },
        ),
        migrations.CreateModel(
            name='SslUntrustedAuxAlert',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('orion_node_id', models.BigIntegerField(db_index=True, help_text='this is the value in this field to SQL join the Orion server database', verbose_name='Orion Node Id')),
                ('ssl_cert_url', models.URLField(verbose_name='SSL certificate URL')),
                ('ssl_cert_subject', models.TextField(verbose_name='SSL certificate subject')),
                ('raised_on', models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='alert raised on')),
                ('enabled', models.BooleanField(db_index=True, default=True, help_text='if this field is disabled, the Orion alert will not be raised', verbose_name='alert enabled')),
                ('self_url', models.URLField(blank=True, null=True, verbose_name='SSL certificate URL')),
                ('ssl_alert_body', models.TextField(verbose_name='alert body')),
                ('ssl_cert_issuer', models.TextField(verbose_name='SSL certificate issuing authority')),
                ('ssl_cert_notes', models.TextField(blank=True, null=True, verbose_name='SSL certificate notes')),
                ('ssl_cert_issuer_notes', models.TextField(blank=True, null=True, verbose_name='SSL certificate issuing authority notes')),
            ],
            options={
                'verbose_name': 'Custom Orion Alert for untrusted SSL certificates',
                'verbose_name_plural': 'Custom Orion Alerts for untrusted SSL certificates',
            },
        ),
    ]
