# Generated by Django 2.1.1 on 2018-10-29 22:10

from django.contrib.auth.models import User, UserManager
from django.db import migrations


def populate_subscribtions(apps, schema_editor):
    emails = (
        'serban.teodorescu@phsa.ca,james.reilly@phsa.ca,ali.rahmat@phsa.ca')
    template_dir = 'ssl_cert_tracker/template/'
    template_prefix = 'email/'

    subscriptions = [
        ('SSL Report', 'ssl_cert_email',
         'common_name,expires_in_x_days,not_before,not_after'),
        ('Expired SSL Report', 'ssl_cert_expired_email',
         'common_name,has_expired_x_days_ago,not_before,not_after'),
        ('Invalid SSL Report', 'ssl_cert_invalid_email',
         'common_name,will_become_valid_in_x_days,not_before,not_after')]

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
                                     template_dir=template_dir,
                                     template_prefix=template_prefix,
                                     template_name=_[1],
                                     headers=_[2])
        _subscription.created_by_id = user.id
        _subscription.updated_by_id = user.id
        _subscription.save()


def truncate(apps, schema_editor):
    subscription = apps.get_model('ssl_cert_tracker', 'Subscription')
    subscription.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('ssl_cert_tracker', '0005_subscription'),
    ]

    operations = [
        migrations.RunPython(populate_subscribtions, reverse_code=truncate)
    ]
