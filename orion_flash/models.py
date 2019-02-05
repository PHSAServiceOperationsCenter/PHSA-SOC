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
import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from ssl_cert_tracker.models import SslCertificate

LOG = logging.getLogger('orion_flash')


class SslAuxAlertError(Exception):
    """
    custom exception wrapper for this module
    """
    pass


class BaseSslAlert(models.Model):
    """
    class for Orion custom alerts related to SSL certificates

    the alerts will show up in Orion when a query joining this table to an
    Orion entity (initially an Orion.Node) is defined in Orion as a custom
    alert

    our application is populating and maintaining this model regularly via
    celery tasks

    the Orion SQL queries joined to models inheriting from this model
    will each represent a specific alert definition

    periodically the Orion server is evaluating the alerts by executing the
    joined query which must filter on silenced = False.
    alerts can be silenced from the django admin by setting the silenced field
    to True

    the django admin link is present in the self_url field. it must be an
    absolute link and it must be always updated in the post_save event
    """
    orion_node_id = models.BigIntegerField(
        _('Orion Node Id'), db_index=True, blank=False, null=False,
        help_text=_(
            'this is the value in this field to'
            ' SQL join the Orion server database'))
    orion_node_port = models.BigIntegerField(
        _('Orion Node TCP Port'), db_index=True, blank=False, null=False)
    cert_url = models.URLField(
        _('SSL certificate URL'), blank=False, null=False)
    cert_subject = models.TextField(
        _('SSL certificate subject'), blank=False, null=False)
    first_raised_on = models.DateTimeField(
        _('alert first raised on'), db_index=True, auto_now_add=True,
        blank=False, null=False)
    last_raised_on = models.DateTimeField(
        _('alert last raised on'), db_index=True, auto_now=True,
        blank=False, null=False)
    silenced = models.BooleanField(
        _('alert is silenced'), db_index=True, default=False, null=False,
        blank=False,
        help_text=_('The Orion server will ignore this row when evaluating'
                    ' alert conditions. Note that this flag will be'
                    ' automatically reset every $configurable_interval'))
    alert_body = models.TextField(
        _('alert body'), blank=False, null=False)
    cert_issuer = models.TextField(
        _('SSL certificate issuing authority'), blank=False, null=False)
    self_url = models.URLField(
        _('Custom SSL alert URL'), blank=True, null=True)
    md5 = models.CharField(
        _('primary key md5 fingerprint'), db_index=True,
        max_length=64, blank=False, null=False)
    cert_notes = models.TextField(
        _('SSL certificate notes'), blank=True, null=True)
    cert_issuer_notes = models.TextField(
        _('SSL certificate issuing authority notes'), blank=True, null=True)
    not_before = models.DateTimeField(
        _('not valid before'), db_index=True, null=False, blank=False)
    not_after = models.DateTimeField(
        _('expires on'), db_index=True, null=False, blank=False)

    def __str__(self):
        return self.cert_subject

    @classmethod
    def exists(cls, orion_node_id, orion_port):
        pass

    @classmethod
    def update_or_create(cls, ssl_certificate_pk):
        """
        create orion custom alert objects

        :arg int ssl_certificate_pk:

            the primary key for retrieving the ssl certificate object

        """
        try:
            ssl_certificate_obj = SslCertificate.objects.get(
                pk=ssl_certificate_pk)
        except SslCertificate.DoesNotExist as err:
            raise SslAuxAlertError from err

        untrusted_ssl_alert = cls.objects.filter(
            orion_node_id=ssl_certificate_obj.orion_id,
            orion_node_port=ssl_certificate_obj.port.port)

        if untrusted_ssl_alert.exists():
            untrusted_ssl_alert = untrusted_ssl_alert.get()

            if untrusted_ssl_alert.ssl_md5 == ssl_certificate_obj.pk_md5:
                """
                the certificate has not changed, just bail
                """
                return 'SSL certificate {} has not changed'.format(
                    untrusted_ssl_alert.ssl_cert_subject)

            untrusted_ssl_alert.ssl_cert_notes = ssl_certificate_obj.notes
            untrusted_ssl_alert.ssl_cert_issuer_notes = \
                ssl_certificate_obj.issuer.notes
            untrusted_ssl_alert.ssl_cert_url = \
                ssl_certificate_obj.absolute_url
            untrusted_ssl_alert.ssl_cert_subject = \
                'CN: {}, O: {}, C:{}'.format(
                    ssl_certificate_obj.common_name,
                    ssl_certificate_obj.organization_name,
                    ssl_certificate_obj.country_name)
            untrusted_ssl_alert.ssl_cert_issuer = \
                'CN: {}, O: {}, C:{}'.format(
                    ssl_certificate_obj.issuer.common_name,
                    ssl_certificate_obj.issuer.organization_name,
                    ssl_certificate_obj.issuer.country_name)
            untrusted_ssl_alert.ssl_alert_body = \
                'Untrusted SSL Certificate'
            msg = 'updated orion alert for SSL certificate CN: {}'.format(
                untrusted_ssl_alert.ssl_cert_subject)

        else:
            untrusted_ssl_alert = cls(
                orion_node_id=ssl_certificate_obj.orion_id,
                orion_node_port=ssl_certificate_obj.port.port,
                ssl_cert_notes=ssl_certificate_obj.notes,
                ssl_cert_issuer_notes=ssl_certificate_obj.issuer.notes,
                ssl_cert_url=ssl_certificate_obj.absolute_url,
                ssl_cert_subject='CN: {}, O: {}, C:{}'.format(
                    ssl_certificate_obj.common_name,
                    ssl_certificate_obj.organization_name,
                    ssl_certificate_obj.country_name),
                ssl_cert_issuer='CN: {}, O: {}, C:{}'.format(
                    ssl_certificate_obj.issuer.common_name,
                    ssl_certificate_obj.issuer.organization_name,
                    ssl_certificate_obj.issuer.country_name),
                ssl_alert_body='Untrusted SSL Certificate'
            )

            msg = 'created orion alert for SSL certificate CN: {}'.format(
                untrusted_ssl_alert.ssl_cert_subject)

        try:
            untrusted_ssl_alert.save()
        except Exception as err:
            raise SslAuxAlertError from err

        return msg

    class Meta:
        abstract = True


class UntrustedSslAlert(BaseSslAlert, models.Model):
    """
    model to join to Orion.Node for alerts regarding untrusted
    SSL certificates

    the filter used in the Orion alert definition is:
    where cert_is_trusted = False and silenced = False

    the model is populated via celery tasks by periodically calling
    :function:`<ssl_cert_tracker.lib.is_not_trusted>` and iterating through
    the queryset.

        *    if the node:port combination exists, check the md5 fingerprint

            *    if the md5 fingerprint matches, check the trust:

                *    if the cert is now trusted, delete the record and bail

                *    otherwise:

                    *    unsilence the alarm

                    *    update the last_raised_on field (this will happen
                         automatically if we just save the record and
                         force an update)

            * otherwise, check the trust:

                *    if not trusted, unsilence the alert and update the
                     whole row

                *    otherwise, delete the row

    the model needs to also be trimmed. use a celery task to iterate
    through each instance. use the node:port combination to extract the
    corresponding row from :class:`<ssl_cert_tracker.models.SslCertificate>`

        *    if a corresponding row is found, check the issuer__is_trusted
             field and delete the alert

        *    otherwise, the certificate doesn't exist anymore so there is no
             alert, delete the alert row
    """
    cert_is_trusted = models.BooleanField(
        _('is trusted'), db_index=True, null=False, blank=False)

    def __str__(self):
        return 'untrusted SSL certificate {}'.format(self.cert_subject)

    class Meta:
        verbose_name = _('Custom Orion Alert for untrusted SSL certificates')
        verbose_name_plural = _(
            'Custom Orion Alerts for untrusted SSL certificates')


class ExpiresSoonSslAlert(BaseSslAlert, models.Model):
    """
    model to join to Orion.Node for alerts regarding SSL certificates that
    will expire in less than a given period of time

    this model is populated via celery tasks periodically calling
    :function:`<ssl_cert_tracker.lib.expires_in>` with various values for the
    lt_days argument and iterating through the queryset returned by said
    function.

    one must define a different Orion alert for each desired lt_days value
    and the filter used in the joined query must match that value.
    lt_days is mapped to the field named 'expires_in_less_than'.

        *    if there is no node:port combination in this model, just
             create the record

        *    if there is a node:port combination matching, check the md5
             value:

            *    if md5 matches, unsilence the alert and update the
                  last_raised_on field

            *    otherwise update the entire row. this is probably a very long
                 shot, it means that a certificate that expires soon has been
                 replaced with another certificate that expires soon

    the model needs to be trimmed. see previous model for ideas
    """
    expires_in = models.BigIntegerField(
        _('expires in'), db_index=True, blank=False, null=False)
    expires_in_lt = models.BigIntegerField(
        _('expires in less than'), db_index=True, blank=False, null=False)

    def __str__(self):
        return 'SSL certificate {} will expire in {} days'.format(
            self.cert_subject, self.expires_in)

    class Meta:
        verbose_name = _('SSL Certificates Expiration Warning')
        verbose_name_plural = _('SSL Certificates Expiration Warnings')


class ExpiredSslAlert(BaseSslAlert, models.Model):
    """
    model to join to Orion.Node for alerts about expires SSL certificates

    see previous model(s) for ideas
    """
    has_expired = models.BigIntegerField(
        _('has expired'), db_index=True, blank=False, null=False)

    def __str__(self):
        return 'SSL certificate {} has expired {} days ago'.format(
            self.cert_subject, self.has_expired)

    class Meta:
        verbose_name = _('Expired SSL Certificates Alert')
        verbose_name_plural = _('Expired SSL Certificates Alerts')


class InvalidSslAlert(BaseSslAlert, models.Model):
    """
    model to join to Orion.Node for alerts about SSL certificates that are
    not yet valid

    see previous model(s) for ideas
    """
    invalid_for = models.BigIntegerField(
        _('will become valid in'), db_index=True, blank=False, null=False)

    def __str__(self):
        return 'SSL certificate {} will become valid in {} days'.format(
            self.cert_subject, self.invalid_for)

    class Meta:
        verbose_name = _('Not Yet Valid SSL Certificates Alert')
        verbose_name_plural = _('Not Yet Valid SSL Certificates Alert')
