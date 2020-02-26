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
from datetime import timedelta
from logging import getLogger

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

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

    # remove None values
    alertable_timings = [d for d in alertable_timings if d]

    threshold = get_preference('citrusborgux__ux_alert_threshold')
    if any(timing > threshold for timing in alertable_timings):
        LOG.info('Slowdown on %s', instance.source_host.host_name)
        raise_citrix_slow_alert.delay(instance.id, threshold.total_seconds())


@receiver(post_save, sender=WinlogEvent)
def failure_cluster_check(sender, instance, *args, **kwargs):
    """
    Send an alert if there has been a cluster of failed winlogevents, as defined
    by the appropriate preferences (TBD).
    """
    if instance.event_state != 'Failed':
        return

    # TODO should be the time of the received event, not now.
    # TODO timeframe should be configurable (eg a dynamic preference)
    recent_failure_count = WinlogEvent.active.filter(
        created_on__gte=timezone.now() - timedelta(minutes=5),
        created_on__lte=timezone.now(), event_state='Failed').count()

    LOG.info('there have been %d failures recently', recent_failure_count)

    # TODO failure threshold should be a dynamic preference
    if recent_failure_count >= 5:
        # TODO actually send alert
        LOG.warning('There have been %d citrix login failures in the last %d'
                    ' minutes', recent_failure_count, 5)
