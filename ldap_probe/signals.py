"""
ldap_probe.signals
------------------

This module contains the `Django signals
<https://docs.djangoproject.com/en/2.2/topics/signals/#module-django.dispatch>`__
for the :ref:`Active Directory Services Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from ldap_probe import ldap_probe_log, tasks

from orion_flash.orion.api import DestSwis


# pylint: disable=unused-argument
@receiver(post_save, sender=ldap_probe_log.LdapProbeLog)
def invoke_raise_ldap_failed_alert(sender, instance, *args, **kwargs):
    """
    evaluate whether the :class:`ldap_probe.models.LdapProbeLog` instance
    is in a failed state and invoke the `Celery task` that is responsible
    for dispatching the alert

    """
    if not instance.node_is_enabled:
        return

    if not instance.failed:
        return

    tasks.raise_ldap_probe_failed_alert.delay(instance.id)


@receiver(post_save, sender=ldap_probe_log.LdapProbeLog)
def invoke_raise_ldap_perf_alert(sender, instance, *args, **kwargs):
    """
    evaluate whether the :class:`ldap_probe.models.LdapProbeLog` instance
    is showing a performance problem and invoke the `Celery task` responsible
    for dispatching a performance alert

    """
    if not instance.node_is_enabled:
        return

    if instance.perf_err:
        tasks.raise_ldap_probe_perf_err.delay(instance.id)
        return

    if instance.perf_alert:
        tasks.raise_ldap_probe_perf_alert.delay(instance.id)
        return

    if instance.perf_warn:
        tasks.raise_ldap_probe_perf_warn.delay(instance.id)

    return

# pylint: enable=unused-argument
