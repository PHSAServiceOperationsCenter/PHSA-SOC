# Generated by Django 2.2.6 on 2020-07-22 21:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ssl_cert_tracker', '0014_externalsslnode'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='externalsslnode',
            options={'verbose_name': 'External node monitored for SSL certificates', 'verbose_name_plural': 'External nodes monitored for SSL certificates'},
        ),
        migrations.AlterField(
            model_name='sslcertificate',
            name='orion_id',
            field=models.BigIntegerField(blank=True, db_index=True, help_text='Orion Node unique identifier  on the Orion server used to show the node in the Orion web console', null=True, verbose_name='orion node identifier'),
        ),
    ]
