# Generated by Django 2.1.4 on 2019-03-15 18:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('orion_flash', '0009_auto_20190314_1555'),
    ]

    operations = [
        migrations.AlterField(
            model_name='citrusborgloginalert',
            name='host_name',
            field=models.CharField(db_index=True, max_length=63, verbose_name='host name'),
        ),
        migrations.AlterField(
            model_name='citrusborguxalert',
            name='host_name',
            field=models.CharField(db_index=True, max_length=63, verbose_name='host name'),
        ),
        migrations.AlterField(
            model_name='deadcitrusbotalert',
            name='host_name',
            field=models.CharField(db_index=True, max_length=63, verbose_name='host name'),
        ),
    ]