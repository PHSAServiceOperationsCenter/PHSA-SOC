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

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from citrus_borg.dynamic_preferences_registry import (get_preference,
                                                      get_int_list_preference)
from citrus_borg.models import EventCluster, WinlogEvent
from citrus_borg.tasks import raise_citrix_slow_alert
from p_soc_auto_base.email import Email
from p_soc_auto_base.utils import get_subscription

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

    # TODO alternately just check if the test passed, if it did there should be
    #      timings if not is it worth alerting?
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
    by the appropriate preferences: citrusborgux__cluster_event_ids.,
    citrusborgux__cluster_length, citrusborgux__cluster_size. See preference
    definitions for more details.
    """
    failure_ids = get_int_list_preference('citrusborgux__cluster_event_ids')
    if instance.event_id not in failure_ids:
        return

    recent_failures = WinlogEvent.active.filter(
        timestamp__gte=instance.timestamp
        - get_preference('citrusborgux__cluster_length'),
        timestamp__lte=instance.timestamp,
        event_id__in=failure_ids,
        cluster__isnull=True
    )
    recent_failures_count = recent_failures.count()

    LOG.debug('there have been %d failures recently', recent_failures_count)

    if recent_failures_count >= get_preference('citrusborgux__cluster_size'):
        # TODO replace this with get_or_create_user when the automated testing
        #      branch is merged (or possibly set it to the default?)
        default_user = \
            get_user_model().objects.get_or_create(username='default')[0]

        new_cluster = EventCluster(
            created_by=default_user, updated_by=default_user
        )

        new_cluster.save()

        new_cluster.winlogevent_set.add(*list(recent_failures))

        # TODO could this be done on the server side?
        # Note that this count includes the cluster we just created, hence <=
        if (len([cluster for cluster in EventCluster.active.all()
                if cluster.end_time > timezone.now()
                - get_preference('citrusborgux__backoff_time')])
                <= get_preference('citrusborgux__backoff_limit')):
            Email.send_email(None, get_subscription('Citrix Cluster Alert'),
                             False, start_time=new_cluster.start_time,
                             end_time=new_cluster.end_time,
                             bots=new_cluster.winlogevent_set.all())
            LOG.debug('sent cluster email')
        else:
            new_cluster.enabled = False
            new_cluster.save()
            LOG.info('Cluster created, but alert skipped due to frequency.')
