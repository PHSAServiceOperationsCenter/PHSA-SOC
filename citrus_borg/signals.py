"""
citrix_borg.signals
-------------------

This module contains the `Django signals
<https://docs.djangoproject.com/en/2.2/topics/signals/#module-django.dispatch>`__
for the :ref:`Citrus Borg Application`.

:copyright:

    Copyright 2018 - 2020 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from logging import getLogger

from django.db.models.signals import post_save
from django.dispatch import receiver

from citrus_borg.dynamic_preferences_registry import get_preference
from citrus_borg.models import WinlogEvent
from citrus_borg.tasks import raise_citrix_slow_alert

LOG = getLogger(__name__)


# To be used as a receiver all these arguments are required (despite not being
# used)
# pylint: disable=unused-argument

@receiver(post_save, sender=WinlogEvent)
def invoke_raise_citrix_slow_alert(sender, instance, *args, **kwargs):
    """
    evaluate whether the :class:`citrus_borg.models.WinlogEvent` instance
    is reporting slower than expected timings and invoke the `Celery task` that
    is responsible for dispatching the alert
    """
    alertable_timings = [instance.storefront_connection_duration,
                         instance.logon_achieved_duration,
                         instance.receiver_startup_duration,
                         instance.connection_achieved_duration,
                         instance.receiver_startup_duration]

    threshold = get_preference('citrusborgux__ux_alert_threshold')
    if any(timing > threshold for timing in alertable_timings):
        LOG.info('Slowdown on %s', instance.source_host.host_name)
        raise_citrix_slow_alert.delay(instance.id, threshold.total_seconds())
