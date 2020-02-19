"""
p_soc_auto_base.migrations
--------------------------

This module contains the migrations for `p_soc_auto_base`. That is migrations
that affect the SOC automation application, but do not belong in a specific
application.

:copyright:

    Copyright 2018 - 2020 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""

from django.contrib.auth.models import User

TO_EMAILS = 'TSCST-Support@hssbc.ca,TSCST-Shiftmanager@hssbc.ca,' \
            'daniel.busto@hssbc.ca'


def create_subscription(apps, subscription_dict):
    """
    Saves a subscription to the database

    :param apps: Django apps instance.
    :param subscription_dict: arguments to set up a subscription, as a dict.
    """
    subscription_model = apps.get_model('ssl_cert_tracker', 'Subscription')

    user = User.objects.filter(is_superuser=True).first()

    # TODO can I have alternate_email_subject='', do we even need the alt?
    subscription_defaults = {
        'emails_list': TO_EMAILS,
        'from_email': 'TSCST-Support@hssbc.ca',
        'template_dir': 'ssl_cert_tracker/template/',
        'template_prefix': 'email/',
        'created_by_id': user.id,
        'updated_by_id': user.id,
        'enabled': True,
    }

    subscription_dict.update(subscription_defaults)

    subscription = subscription_model(**subscription_dict)

    subscription.save()
