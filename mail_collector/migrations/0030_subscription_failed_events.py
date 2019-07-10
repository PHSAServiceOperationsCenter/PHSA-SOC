# Generated by Django 2.1.4 on 2019-07-09 20:37
from django.contrib.auth.models import User, UserManager

from django.db import migrations


def add_subscriptions(apps, schema_editor):
    to_emails = ('TSCST-Support@hssbc.ca,TSCST-Shiftmanager@hssbc.ca')

    subscriptions = [
        {
            'subscription': 'Exchange Client Error',
            'enabled': True,
            'emails_list': to_emails,
            'from_email': 'TSCST-Support@hssbc.ca',
            'template_dir': 'mail_collector/templates',
            'template_name': 'event_error',
            'template_prefix': 'email/',
            'email_subject':
            '',
            'alternate_email_subject':
            '',
            'headers': (
                'uuid,event_message,event_exception,event_body,event_registered_on'),
        },
    ]

    subscription_model = apps.get_model('ssl_cert_tracker', 'subscription')

    user = User.objects.filter(is_superuser=True)
    if user.exists():
        user = user.first()
    else:
        user = User.objects.create(
            username='soc_su', email='soc_su@phsa.ca',
            password='soc_su_password', is_active=True, is_staff=True,
            is_superuser=True)
        user.set_password('soc_su_password')
        user.save()

    for subscription in subscriptions:
        subscription.update(dict(created_by_id=user.id, updated_by_id=user.id))
        subscription_instance = subscription_model(**subscription)
        subscription_instance.save()


class Migration(migrations.Migration):

    dependencies = [
        ('mail_collector', '0029_subscription_exc_fail_evts_site'),
    ]

    operations = [
        migrations.RunPython(add_subscriptions,
                             reverse_code=migrations.RunPython.noop)
    ]
