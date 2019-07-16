# Generated by Django 2.1.4 on 2019-06-11 17:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('mail_collector', '0011_auto_20190610_1151'),
    ]

    operations = [
        migrations.AddField(
            model_name='exchangedatabase',
            name='enabled',
            field=models.BooleanField(db_index=True, default=True, verbose_name='Enabled'),
        ),
        migrations.AddField(
            model_name='exchangeserver',
            name='enabled',
            field=models.BooleanField(db_index=True, default=True, verbose_name='Enabled'),
        ),
    ]