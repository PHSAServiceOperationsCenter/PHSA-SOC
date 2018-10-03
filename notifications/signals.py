"""
.. _signals:

signals module: contains functions that need be invoked from
django signals raised by the notification application

:module:    p_soc_auto.notification.signals

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

:update:    Oct. 03 2018

"""
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import send_email

from .models import Notification, NotificationLevel


@receiver(post_save, sender=Notification)
def broadcast_notification(sender, instance, *args, **kwargs):
    """
    invoke tasks required by a broadcast action

    these tasks need to be invoked when a notification does not have
    a broadcast_on attribute or, to be more procise, when the broadcast_on
    value is set to None. which suggests that if one wants to rebroadcast
    every damn notification, one can just clear the value fo that field

    we broadcast selectively based on the value of the
    settings.NOTIFICATION_BROADCAST_LEVELS variable.
    if it has not been defined, we broadcast for all levels, otherwise we
    only broadcast for those levels specified therein
    """
    if instance.broadcast_on is not None:
        # has been broadcast already, bail
        return

    if hasattr(settings, 'NOTIFICATION_BROADCAST_LEVELS'):
        # we have predefined levels
        # is this a level that we notify for
        if instance.notification_level not in \
                NotificationLevel.objects.\
                filter(notification_level__in=settings.
                       NOTIFICATION_BROADCAST_LEVELS):
            return

    broadcast_methods = list(
        instance.notification_type.notification_broadcast.
        all().values_list('broadcast', flat=True)
    )

    if 'log' in broadcast_methods:
        print('it has already been logged')
    if 'email' in broadcast_methods:
        send_email(instance.pk, 'broadcast_on')
    if 'sms' in broadcast_methods:
        print('not yet implemented')
    if 'orion_alert' in broadcast_methods:
        print('not yet implemented')
