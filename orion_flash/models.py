"""
.. _models:

django models module for the orion_flash app

:module:    p_soc_auto.orion_flash.models

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Jan. 15, 2019

"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class SslAuxAlertBase(models.Model):
    """
    base class for Orion custom alerts

    the alerts defined in Orion as cusotm SQL alerts joining the Orion Node
    against any of the tables in this database

    our application is populating (and de-populating these models)
    periodically. the Orion server is evaluating the alerts by executing the
    joined query. the joined query will filter on the alert_enabled field.

    the tables will contain the instance link (populated during post-save
    because we need the pk value to create it) and one will be able to
    disable the alert by opening said link
    """
    orion_node_id = models.BigIntegerField(
        _('Orion Node Id'), db_index=True, blank=False, null=False,
        help_text=_(
            'this is the value in this field to'
            ' SQL join the Orion server database'))
    ssl_cert_url = models.URLField(
        _('SSL certificate URL'), blank=False, null=False)
    ssl_cert_subject = models.TextField(
        _('SSL certificate subject'), blank=False, null=False)
    raised_on = models.DateTimeField(
        _('alert raised on'), db_index=True, auto_now_add=True, blank=False,
        null=False)
    enabled = models.BooleanField(
        _('alert enabled'), db_index=True, default=True, null=False, blank=False,
        help_text=_(
            'if this field is disabled, the Orion alert will not be raised'))
    self_url = models.URLField(
        _('SSL certificate URL'), blank=True, null=True)
    ssl_alert_body = models.TextField(
        _('alert body'), blank=False, null=False)

    class Meta:
        abstract = True


class SslUntrustedAuxAlert(SslAuxAlertBase, models.Model):
    """
    model for raising orion alerts on SSL certificates that are not trusted

    this  is a YoYo model:

        * we will populate via a task that is also responsible for purging
          the model

        * we need to figure out if we can save the admin change links
          within the model itself so that we can pull them into the
          Orion alert message. if we have the links there, we can disable the
          alerts here after they are first raised

    the idea is to use where enabled = True when writing the custom SQL
    alert in Orion and also to configure the alert to be checked periodically.
    so if we (can) provide a link to disable the alert in this model, the Orion
    alert will trigger anymore

    the self url(s) need to be created in the post-save signal
    """
    ssl_cert_issuer = ssl_cert_subject = models.TextField(
        _('SSL certificate issuing authority'), blank=False, null=False)
    ssl_cert_notes = models.TextField(
        _('SSL certificate notes'), blank=True, null=True)
    ssl_cert_issuer_notes = models.TextField(
        _('SSL certificate issuing authority notes'), blank=True, null=True)

    def __str__(self):
        return self.ssl_cert_subject

    class Meta:
        app_label = 'orion_flash'
        verbose_name = _('Custom Orion Alert for untrusted SSL certificates')
        verbose_name_plural = _(
            'Custom Orion Alerts for untrusted SSL certificates')


class SslInvalidAuxAlert(SslAuxAlertBase, models.Model):
    not_before = models.DateTimeField(
        _('not valid before'), db_index=True, null=False, blank=False)
    not_after = models.DateTimeField(
        _('expires on'), db_index=True, null=False, blank=False)
