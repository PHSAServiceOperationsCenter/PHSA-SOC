"""
ldap_probe.signals
------------------

This module contains the `Django signals
<https://docs.djangoproject.com/en/2.2/topics/signals/#module-django.dispatch>`__
for the :ref:`Active Directory Services Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca
:contact:    daniel.busto@phsa.ca

:updated:    Dec. 11, 2019

"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from ldap_probe import models, tasks

# pylint: disable=unused-argument


@receiver(post_save, sender=models.LdapProbeLog)
def invoke_raise_ldap_failed_alert(sender, instance, *args, **kwargs):
    """
    evaluate whether the :class:`ldap_probe.models.LdapProbeLog` instance
    is in a failed state and invoke the `Celery task` that is responsible
    for dispatching the alert

    """
    if not instance.failed:
        return

    tasks.raise_ldap_probe_failed_alert.delay(instance.id)


@receiver(post_save, sender=models.LdapProbeLog)
def invoke_raise_ldap_perf_alert(sender, instance, *args, **kwargs):
    """
    evaluate whether the :class:`ldap_probe.models.LdapProbeLog` instance
    is showing a performance problem and invoke the `Celery task` responsible
    for dispatching a performance alert

    """
    if instance.perf_alert:
        tasks.raise_ldap_probe_perf_alert.delay(instance.id)
        return

    if instance.perf_warn:
        tasks.raise_ldap_probe_perf_warn.delay(instance.id)

    return

# pylint: enable=unused-argument
