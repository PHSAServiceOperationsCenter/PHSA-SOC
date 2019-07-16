# Generated by Django 2.1.4 on 2019-06-27 21:20
from django.contrib.auth.models import User, UserManager
from django.db import migrations


def add_subscriptions(apps, schema_editor):
    to_emails = ('TSCST-Support@hssbc.ca,TSCST-Shiftmanager@hssbc.ca')

    subscriptions = [
        {
            'subscription': 'Exchange Client Bots Not Seen',
            'enabled': True,
            'emails_list': to_emails,
            'from_email': 'TSCST-Support@hssbc.ca',
            'template_dir': 'mail_collector/templates',
            'template_name': 'exc_serv_alert_all',
            'template_prefix': 'email/',
            'email_subject':
            'Exchange client bots that have not made any mail requests over the last',
            'alternate_email_subject':
            'All Exchange client bots have been functioning properly over the last',
            'headers': ('host_name,site__site,excgh_last_seen'),
        },
        {
            'subscription': 'Exchange Client Bot Sites Not Seen',
            'enabled': True,
            'emails_list': to_emails,
            'from_email': 'TSCST-Support@hssbc.ca',
            'template_dir': 'mail_collector/templates',
            'template_name': 'exc_serv_alert_all',
            'template_prefix': 'email/',
            'email_subject':
            'Exchange client bot sites that have not made any mail requests over the last',
            'alternate_email_subject':
            'At least one Exchange client bot has been functioning properly on each site over the last',
            'headers': ('site__site.most_recent'),
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
        ('mail_collector', '0021_auto_20190627_1213'),
    ]

    operations = [
        migrations.RunPython(add_subscriptions,
                             reverse_code=migrations.RunPython.noop)
    ]