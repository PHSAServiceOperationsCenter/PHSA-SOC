# Generated by Django 2.2.6 on 2019-12-06 21:42
from django.contrib.auth.models import User, UserManager

from django.db import migrations


def add_subscriptions(apps, schema_editor):
    to_emails = (
        'TSCST-Support@hssbc.ca,TSCST-Shiftmanager@hssbc.ca,'
        'serban.teodorescu@phsa.ca,daniel.busto@phsa.ca')

    subscriptions = [
        {
            'subscription': 'LDAP: error report',
            'enabled': True,
            'emails_list': to_emails,
            'from_email': 'TSCST-Support@hssbc.ca',
            'template_dir': 'ssl_cert_tracker/templates',
            'template_name': 'ldap_error_report',
            'template_prefix': 'email/',
            'email_subject': 'AD Services Monitoring Errors',
            'alternate_email_subject': '',
            'headers': (
                'uuid,domain_controller_fqdn,created_on,errors,probe_url'),
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
        ('ldap_probe', '0026_beats_for_perf_summary_reports'),
    ]

    operations = [
        migrations.RunPython(add_subscriptions,
                             reverse_code=migrations.RunPython.noop)
    ]
