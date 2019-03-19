# Generated by Django 2.1.4 on 2019-02-04 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ssl_cert_tracker', '0022_add_more_tasks'),
    ]

    operations = [
        migrations.AlterField(
            model_name='sslcertificate',
            name='pk_md5',
            field=models.CharField(db_index=True, max_length=64, verbose_name='primary key md5 fingerprint'),
        ),
        migrations.AlterField(
            model_name='sslcertificate',
            name='pk_sha1',
            field=models.TextField(verbose_name='primary key sha1 fingerprint'),
        ),
    ]
