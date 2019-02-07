"""
.. _signals:

signals module for the orion_flash app

:module:    p_soc_auto.orion_flash.signals

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Feb. 6, 2019

"""
import socket

from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse

from .models import (
    UntrustedSslAlert, ExpiresSoonSslAlert, ExpiredSslAlert, InvalidSslAlert,
)


@receiver(post_save, sender=UntrustedSslAlert)
@receiver(post_save, sender=ExpiredSslAlert)
@receiver(post_save, sender=ExpiresSoonSslAlert)
@receiver(post_save, sender=InvalidSslAlert)
def update_local_url(sender, instance, created, *args, **kwargs):
    """
    add an URL to self in the instance

    this is needed because we want to provide a link back from the Orion alert
    body. this link would be used to silence the alarm
    """
    if created:
        instance.self_url = '{}://{}:{}/{}'.format(
            settings.SERVER_PROTO, socket.getfqdn(), settings.SERVER_PORT,
            reverse(
                'admin:orion_flash_{}_change'.format(sender._meta.model_name),
                args=(instance.id,)))
        instance.save()

    return
