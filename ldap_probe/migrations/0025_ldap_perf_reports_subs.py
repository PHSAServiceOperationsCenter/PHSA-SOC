# Generated by Django 2.2.6 on 2019-12-05 19:54
from django.contrib.auth.models import User, UserManager

from django.db import migrations


def add_subscriptions(apps, schema_editor):
    to_emails = (
        'TSCST-Support@hssbc.ca,TSCST-Shiftmanager@hssbc.ca,'
        'serban.teodorescu@phsa.ca,daniel.busto@phsa.ca')

    subscriptions = [
        {
            'subscription': 'LDAP: summary report, anonymous bind, perf, non orion',
            'enabled': True,
            'emails_list': to_emails,
            'from_email': 'TSCST-Support@hssbc.ca',
            'template_dir': 'ssl_cert_tracker/templates',
            'template_name': 'ldap_summary_report',
            'template_prefix': 'email/',
            'email_subject': 'AD Services Monitoring Performance Degradation Summary Report, bind duration greater than',
            'alternate_email_subject': '',
            'headers': (
                'node_dns,number_of_failed_probes,'
                'number_of_successfull_probes,average_initialize_duration,'
                'minimum_bind_duration,average_bind_duration,'
                'maximum_bind_duration,minimum_read_root_dse_duration,'
                'average_read_root_dse_duration,'
                'maximum_read_root_dse_duration,orion_url,probes_url'),
        },
        {
            'subscription': 'LDAP: summary report, anonymous bind, perf, orion',
            'enabled': True,
            'emails_list': to_emails,
            'from_email': 'TSCST-Support@hssbc.ca',
            'template_dir': 'ssl_cert_tracker/templates',
            'template_name': 'ldap_summary_report',
            'template_prefix': 'email/',
            'email_subject': 'AD Services Monitoring Performance Degradation Summary Report, bind duration greater than',
            'alternate_email_subject': '',
            'headers': (
                'node__node_caption,orion_anchor,number_of_failed_probes,'
                'number_of_successfull_probes,average_initialize_duration,'
                'minimum_bind_duration,average_bind_duration,'
                'maximum_bind_duration,minimum_read_root_dse_duration,'
                'average_read_root_dse_duration,'
                'maximum_read_root_dse_duration,orion_url,probes_url'),
        },
        {
            'subscription': 'LDAP: summary report, full bind, perf, non orion',
            'enabled': True,
            'emails_list': to_emails,
            'from_email': 'TSCST-Support@hssbc.ca',
            'template_dir': 'ssl_cert_tracker/templates',
            'template_name': 'ldap_summary_report',
            'template_prefix': 'email/',
            'email_subject': 'AD Services Monitoring Performance Degradation Summary Report, bind duration greater than',
            'alternate_email_subject': '',
            'headers': (
                'node_dns,number_of_failed_probes,'
                'number_of_successfull_probes,average_initialize_duration,'
                'minimum_bind_duration,average_bind_duration,'
                'maximum_bind_duration,minimum_extended_search_duration,'
                'average_extended_search_duration,'
                'maximum_extended_search_duration,orion_url,probes_url'),
        },
        {
            'subscription': 'LDAP: summary report, full bind, perf, orion',
            'enabled': True,
            'emails_list': to_emails,
            'from_email': 'TSCST-Support@hssbc.ca',
            'template_dir': 'ssl_cert_tracker/templates',
            'template_name': 'ldap_summary_report',
            'template_prefix': 'email/',
            'email_subject': 'AD Services Monitoring Performance Degradation Summary Report, bind duration greater than',
            'alternate_email_subject': '',
            'headers': (
                'node__node_caption,orion_anchor,number_of_failed_probes,'
                'number_of_successfull_probes,average_initialize_duration,'
                'minimum_bind_duration,average_bind_duration,'
                'maximum_bind_duration,minimum_extended_search_duration,'
                'average_extended_search_duration,'
                'maximum_extended_search_duration,orion_url,probes_url'),
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
        ('ldap_probe', '0023_add_subscriptions_ldap_summary_reports'),
    ]

    operations = [
        migrations.RunPython(add_subscriptions,
                             reverse_code=migrations.RunPython.noop)
    ]
