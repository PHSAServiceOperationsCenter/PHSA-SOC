# Generated by Django 2.1.1 on 2018-11-22 23:06

from django.db import migrations
from django.conf import settings
from django.contrib.auth.models import User


def populate_event_sources(apps, schema_editor):
    model = apps.get_model('citrus_borg', 'AllowedEventSource')

    user = User.objects.filter(username=settings.CITRUS_BORG_SERVICE_USER)
    if user.exists():
        user = user.get()
    else:
        user = User.objects.create_user(settings.CITRUS_BORG_SERVICE_USER)

    event_source = model(source_name='ControlUp Logon Monitor')
    event_source.created_by_id = user.id
    event_source.updated_by_id = user.id

    event_source.save()


def reverse_this(apps, schema_editor):
    model = apps.get_model('citrus_borg', 'AllowedEventSource')

    model.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('citrus_borg', '0002_auto_20181122_1502'),
    ]

    operations = [
        migrations.RunPython(populate_event_sources, reverse_code=reverse_this)
    ]
