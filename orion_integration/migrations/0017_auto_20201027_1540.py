# Generated by Django 2.2.6 on 2020-10-27 22:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('orion_integration', '0016_auto_20200420_0928'),
    ]

    operations = [
        migrations.RenameField(
            model_name='orionapmapplication',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='orionnode',
            old_name='created_on',
            new_name='created',
        ),
        migrations.RenameField(
            model_name='orionnodecategory',
            old_name='created_on',
            new_name='created',
        ),
    ]
