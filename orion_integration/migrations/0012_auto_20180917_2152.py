# Generated by Django 2.1.1 on 2018-09-17 21:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orion_integration', '0011_auto_20180905_2208'),
    ]

    operations = [
        migrations.AlterField(
            model_name='orionnode',
            name='node_dns',
            field=models.CharField(blank=True, db_index=True, max_length=254, null=True, verbose_name='DNS'),
        ),
    ]