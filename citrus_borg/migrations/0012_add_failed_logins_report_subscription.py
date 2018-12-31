# Generated by Django 2.1.1 on 2018-12-31 18:49
from django.contrib.auth.models import User, UserManager
from django.db import migrations


def add_subscribtions(apps, schema_editor):
    emails = (
        'serban.teodorescu@phsa.ca,james.reilly@phsa.ca'
        ',TSCST-Support@hssbc.ca,TSCST-Shiftmanager@hssbc.ca')
    from_email = 'TSCST-Support@hssbc.ca'
    template_dir = 'ssl_cert_tracker/template/'
    template_prefix = 'email/'

    subscriptions = [
        ('Citrix Failed Logins Report', 'borg_failed_logins_report',
         'created_on,source_host__site__site,source_host__host_name'
         ',failure_reason,failure_details'), ]

    subscription = apps.get_model('ssl_cert_tracker', 'Subscription')

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

    for _ in subscriptions:
        _subscription = subscription(subscription=_[0],
                                     emails_list=emails,
                                     from_email=from_email,
                                     template_dir=template_dir,
                                     template_prefix=template_prefix,
                                     template_name=_[1],
                                     headers=_[2])
        _subscription.created_by_id = user.id
        _subscription.updated_by_id = user.id
        _subscription.save()


class Migration(migrations.Migration):

    dependencies = [
        ('citrus_borg', '0011_merge_20181205_1600'),
    ]

    operations = [
        migrations.RunPython(
            add_subscribtions, reverse_code=migrations.RunPython.noop)
    ]