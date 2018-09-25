# Generated by Django 2.1.1 on 2018-09-25 22:23

from django.db import migrations
from django.conf import settings
from django.contrib.auth.models import User


def populate_notification_type(apps, schema_editor):
    notification_types = [
        dict(notification_type='internal', is_default=False),
        dict(notificaton_type='basic_rule', is_default=True),
        dict(notification_type='ssl_rule', is_default=False)]

    model = apps.get_model('notifications', 'NotificationType')

    user = User.objects.filter(username=settings.NOTIFICATIONS_SERVICE_USER)
    if user.exists():
        user = user.get()
    else:
        user = User.objects.create_user(settings.NOTIFICATIONS_SERVICE_USER)

    for notification_type in notification_types:
        new_notification_type = model(**notification_type)
        new_notification_type.created_by_id = user.id
        new_notification_type.updated_by_id = user.id
        new_notification_type.save()


def truncate_notification_type(apps, schema_editor):
    model = apps.get_model('notifications', 'NotificationType')

    model.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('notifications', '0004_populate_broadcast'),
    ]

    operations = [
        migrations.RunPython(populate_notification_type,
                             reverse_code=truncate_notification_type)
    ]
