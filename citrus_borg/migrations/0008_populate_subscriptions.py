# Generated by Django 2.1.1 on 2018-11-29 19:23

from django.db import migrations
from django.contrib.auth.models import User, UserManager


def populate_subscribtions(apps, schema_editor):
    emails = (
        'serban.teodorescu@phsa.ca,james.reilly@phsa.ca')
    template_dir = 'ssl_cert_tracker/template/'
    template_prefix = 'email/'

    subscriptions = [
        ('Dead Citrix monitoring bots', 'borg_hosts_dead_email',
         'host_name,ip_address,site__site,last_seen'),
        ('Dead Citrix client sites', 'borg_sites_dead_email',
         'site,winlogbeathost__last_seen'),
        ('Missing Citrix farm hosts', 'borg_servers_dead_email',
         'broker_name,last_seen')]

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

    try:
        subscription.objects.all().delete()
    except:
        pass

    for _ in subscriptions:
        _subscription = subscription(subscription=_[0],
                                     emails_list=emails,
                                     template_dir=template_dir,
                                     template_prefix=template_prefix,
                                     template_name=_[1],
                                     headers=_[2])
        _subscription.created_by_id = user.id
        _subscription.updated_by_id = user.id
        _subscription.save()


class Migration(migrations.Migration):

    dependencies = [
        ('citrus_borg', '0007_populate_bots'),
    ]

    operations = [
        migrations.RunPython(populate_subscribtions,
                             reverse_code=migrations.RunPython.noop)
    ]
