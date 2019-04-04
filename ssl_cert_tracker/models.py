"""
.. _models:

django models for the ssl_certificates app

:module:    ssl_certificates.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""
import socket

from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from citrus_borg.dynamic_preferences_registry import get_preference
from orion_integration.models import OrionNode
from p_soc_auto_base.models import BaseModel

from .lib import expires_in, has_expired, is_not_yet_valid


class ExpiresIn(models.Manager):
    """
    custom manager class
    """

    def get_queryset(self):
        """
        return only valid certificates sorted by expiration date ascending
        """
        return expires_in()


class ExpiredSince(models.Manager):
    """
    show expired SSL certificates
    """

    def get_queryset(self):
        """
        only expired certificates
        """
        return has_expired()


class NotYetValid(models.Manager):
    """
    custom manager class to show certificates that are not yet valid
    """

    def get_queryset(self):
        """
        need to override this method to return our stuff
        """
        return is_not_yet_valid()


class SslCertificateBase(BaseModel, models.Model):
    """
    base model for SSL certificate models
    """
    common_name = models.CharField(
        _('common name'), db_index=True, max_length=253, blank=True,
        null=True, help_text=_('SSL certificate commonName field'))
    organization_name = models.CharField(
        _('organization name'), db_index=True, max_length=253, blank=True,
        null=True, help_text=_('SSL certificate organizationName field'))
    country_name = models.CharField(
        _('country name'), db_index=True, max_length=2, blank=True, null=True,
        help_text=_('SSL certificate countryName field'))

    class Meta:
        abstract = True


class SslProbePort(BaseModel, models.Model):
    """
    probe fro SSL certs on all these ports
    """
    port = models.PositiveIntegerField(
        _('port'), unique=True, db_index=True, blank=False, null=False)

    def __str__(self):
        return '%s' % self.port

    class Meta:
        app_label = 'ssl_cert_tracker'
        verbose_name = _('Network Port')
        verbose_name_plural = _('Network Ports')


class SslCertificateIssuer(SslCertificateBase, models.Model):
    """
    model for SSL certificate issujing authorities
    """
    is_trusted = models.BooleanField(
        _('is trusted'), db_index=True, default=False, null=False, blank=False,
        help_text=_('is this a known SSL issuing authority'
                    ' (like Verisign or DigiCert)?'))

    @classmethod
    def get_or_create(
            cls, ssl_issuer, username=settings.NMAP_SERVICE_USER):
        """
        create and return an issuing authority if it doesn't already exist

        if it exists already, just return it
        """
        ssl_certificate_issuer = cls._meta.model.objects.\
            filter(common_name__iexact=ssl_issuer.get('commonName'))
        if ssl_certificate_issuer.exists():
            return ssl_certificate_issuer.get()

        user = cls.get_or_create_user(username)
        ssl_certificate_issuer = cls(
            common_name=ssl_issuer.get('commonName'),
            organization_name=ssl_issuer.get('organizationName'),
            country_name=ssl_issuer.get('countryName'),
            created_by=user, updated_by=user)
        ssl_certificate_issuer.save()

        return ssl_certificate_issuer

    def __str__(self):
        return 'commonName: %s, organizationName: %s' % \
            (self.common_name, self.organization_name)

    class Meta:
        app_label = 'ssl_cert_tracker'
        verbose_name = _('Issuing Authority for SSL Certificates')
        verbose_name_plural = _('Issuing Authorities for SSL Certificates')


class SslCertificate(SslCertificateBase, models.Model):
    """
    SSL certificate data
    """
    orion_id = models.BigIntegerField(
        _('orion node identifier'), blank=False, null=False, db_index=True,
        help_text=_('Orion Node unique identifier  on the Orion server'
                    ' used to show the node in the Orion web console'))
    port = models.ForeignKey(
        SslProbePort, db_index=True, blank=False, null=False,
        verbose_name=_('TCP port'), on_delete=models.PROTECT)
    issuer = models.ForeignKey(
        SslCertificateIssuer, db_index=True, blank=True, null=True,
        verbose_name=_('Issued By'), on_delete=models.PROTECT)
    hostnames = models.TextField(_('host names'), blank=False, null=False)
    not_before = models.DateTimeField(
        _('not valid before'), db_index=True, null=False, blank=False)
    not_after = models.DateTimeField(
        _('expires on'), db_index=True, null=False, blank=False)
    pem = models.TextField(_('PEM'), null=False, blank=False)
    pk_bits = models.CharField(
        _('private key bits'), max_length=4, db_index=True,
        blank=False, null=False)
    pk_type = models.CharField(
        _('primary key type'), max_length=4, db_index=True,
        blank=False, null=False)
    pk_md5 = models.CharField(
        _('primary key md5 fingerprint'), db_index=True,
        max_length=64, blank=False, null=False)
    pk_sha1 = models.TextField(
        _('primary key sha1 fingerprint'), blank=False, null=False)
    last_seen = models.DateTimeField(
        _('last seen'), db_index=True, blank=False, null=False)

    def __str__(self):
        return (
            'CN: {}, O: {}, c: {}'
        ).format(
            self.common_name, self.organization_name, self.country_name)

    @classmethod
    def create_or_update(cls, orion_id, ssl_certificate,
                         username=settings.NMAP_SERVICE_USER):
        """
        create or update the representation of an SSL certificate in the
        database

        if the SSL certificate already exists, just update the last_seen
        field

        return the SSL certificate
        """
        user = cls.get_or_create_user(username)
        issuer = SslCertificateIssuer.get_or_create(
            ssl_certificate.ssl_issuer, username)

        ssl_obj = cls._meta.model.objects.filter(
            orion_id=orion_id, port__port=ssl_certificate.port)

        if ssl_obj.exists():
            ssl_obj = ssl_obj.get()
            if ssl_obj.pk_md5 != ssl_certificate.ssl_md5:
                """
                host and port are the same but the checksum has changed,
                ergo the certificate has been replaced. we need to save
                the new data
                """
                ssl_obj.common_name = ssl_certificate.ssl_subject.\
                    get('commonName')
                ssl_obj.organization_name = ssl_certificate.ssl_subject.\
                    get('organizationName')
                ssl_obj.country_name = ssl_certificate.ssl_subject.\
                    get('countryName')
                ssl_obj.issuer = issuer
                ssl_obj.hostnames = ssl_certificate.hostnames
                ssl_obj.not_before = ssl_certificate.ssl_not_before
                ssl_obj.not_after = ssl_certificate.ssl_not_after
                ssl_obj.pem = ssl_certificate.ssl_pem
                ssl_obj.pk_bits = ssl_certificate.ssl_pk_bits
                ssl_obj.pk_type = ssl_certificate.ssl_pk_type
                ssl_obj.pk_md5 = ssl_certificate.ssl_md5
                ssl_obj.pk_sha1 = ssl_certificate.ssl_sha1
                ssl_obj.updated_by = user

            ssl_obj.last_seen = timezone.now()
            ssl_obj.save()

            return False, ssl_obj

        port = SslProbePort.objects.get(port=int(ssl_certificate.port))
        ssl_obj = cls(
            common_name=ssl_certificate.ssl_subject.get('commonName'),
            organization_name=ssl_certificate.ssl_subject.get(
                'organizationName'),
            country_name=ssl_certificate.ssl_subject.get('countryName'),
            orion_id=orion_id, port=port, issuer=issuer,
            hostnames=ssl_certificate.hostnames,
            not_before=ssl_certificate.ssl_not_before,
            not_after=ssl_certificate.ssl_not_after,
            pem=ssl_certificate.ssl_pem, pk_bits=ssl_certificate.ssl_pk_bits,
            pk_type=ssl_certificate.ssl_pk_type,
            pk_md5=ssl_certificate.ssl_md5, pk_sha1=ssl_certificate.ssl_sha1,
            created_by=user, updated_by=user, last_seen=timezone.now())
        ssl_obj.save()

        return True, ssl_obj

    @property
    @mark_safe
    def node_admin_url(self):
        """
        admin link to the Orion node where the certificate resides
        """
        orion_node = OrionNode.objects.filter(orion_id=self.orion_id)
        if orion_node.exists():
            orion_node = orion_node.get()
            return '<a href="%s">%s on django</>' % (
                reverse('admin:orion_integration_orionnode_change',
                        args=(orion_node.id,)),
                orion_node.node_caption)

        return 'acquired outside the Orion infrastructure'

    @property
    @mark_safe
    def absolute_url(self):
        """
        we need the absolute url to pass around
        """
        return '<a href="{proto}://{host}:{port}/{path}'.format(
            proto=settings.SERVER_PROTO, host=socket.getfqdn(),
            port=settings.SERVER_PROTO,
            path=reverse('admin:ssl_cert_tracker_sslcertificate_change',
                         args=(self.id,)))

    @property
    @mark_safe
    def orion_node_url(self):
        """
        link to the Orion Node object on the Orion server
        """
        orion_node = OrionNode.objects.filter(orion_id=self.orion_id)
        if orion_node.exists():
            orion_node = orion_node.values('node_caption', 'details_url')[0]
            return '<a href="%s%s">%s on Orion</>' % (
                get_preference('orionserverconn__orion_server_url'),
                orion_node.get('details_url'), orion_node.get('node_caption')
            )

        return 'acquired outside the Orion infrastructure'

    class Meta:
        app_label = 'ssl_cert_tracker'
        verbose_name = _('SSL Certificate (new)')
        verbose_name_plural = _('SSL Certificates (new)')
        unique_together = (('orion_id', 'port'),)


class SslExpiresIn(SslCertificate):
    """
    proxy model for valid SSL certificates sorted by expiration date
    """
    objects = ExpiresIn()

    class Meta:
        proxy = True
        verbose_name = 'Valid SSL Certificate'
        verbose_name_plural = 'Valid SSL Certificates by expiration date'


class SslHasExpired(SslCertificate):
    """
    proxy model for valid SSL certificates sorted by expiration date
    """
    objects = ExpiredSince()

    class Meta:
        proxy = True
        verbose_name = 'SSL Certificate: expired'
        verbose_name_plural = 'SSL Certificates: expired'


class SslNotYetValid(SslCertificate):
    """
    proxy model for not yet valid SSL certificates
   """
    objects = NotYetValid()

    class Meta:
        proxy = True
        verbose_name = 'SSL Certificate: not yet valid'
        verbose_name_plural = 'SSL Certificates: not yet valid'


class Subscription(BaseModel):
    subscription = models.CharField(
        'subscription', max_length=64, unique=True, db_index=True, blank=False,
        null=False)
    emails_list = models.TextField('subscribers', blank=False, null=False)
    from_email = models.CharField(
        'from', max_length=255, blank=True, null=True,
        default=settings.DEFAULT_FROM_EMAIL)
    template_dir = models.CharField(
        'email templates directory', max_length=255, blank=False, null=False)
    template_name = models.CharField(
        'email template name', max_length=64, blank=False, null=False)
    template_prefix = models.CharField(
        'email template prefix', max_length=64, blank=False, null=False,
        default='email/')
    email_subject = models.TextField(
        'email subject fragment', blank=True, null=True,
        help_text=('this is the conditional subject of the email template.'
                   ' it is normally just a fragment that will augmented'
                   ' by other variables'))
    alternate_email_subject = models.TextField(
        'fallback email subject', blank=True, null=True,
        help_text='this is the non conditional subject of the email template.')
    headers = models.TextField(
        'data headers', blank=False, null=False,
        default='common_name,expires_in,not_before,not_after')

    def __str__(self):
        return self.subscription

    class Meta:
        app_label = 'ssl_cert_tracker'
