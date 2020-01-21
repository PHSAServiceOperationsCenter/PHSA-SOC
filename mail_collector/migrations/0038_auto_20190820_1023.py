# Generated by Django 2.2.3 on 2019-08-20 17:23

import django.core.validators
from django.db import migrations, models
import re


class Migration(migrations.Migration):

    dependencies = [
        ('mail_collector', '0034_auto_20190806_1409'),
    ]

    operations = [
        migrations.AlterField(
            model_name='domainaccount',
            name='domain',
            field=models.CharField(db_index=True, max_length=15, validators=[django.core.validators.RegexValidator(re.compile('^[-a-zA-Z0-9_]+\\Z'), "Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.", 'invalid')], verbose_name='windows domain'),
        ),
        migrations.AlterField(
            model_name='domainaccount',
            name='username',
            field=models.CharField(db_index=True, max_length=64, validators=[django.core.validators.RegexValidator(re.compile('^[-a-zA-Z0-9_]+\\Z'), "Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.", 'invalid')], verbose_name='domain username'),
        ),
        migrations.AlterField(
            model_name='exchangeconfiguration',
            name='config_name',
            field=models.CharField(db_index=True, max_length=64, unique=True, validators=[django.core.validators.RegexValidator(re.compile('^[-a-zA-Z0-9_]+\\Z'), "Enter a valid 'slug' consisting of letters, numbers, underscores or hyphens.", 'invalid')], verbose_name='name'),
        ),
    ]
