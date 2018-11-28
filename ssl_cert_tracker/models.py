"""
.. _models:

django models for the ssl_certificates app

:module:    ssl_certificates.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils.safestring import mark_safe
from simple_history.models import HistoricalRecords

from p_soc_auto_base.models import BaseModel
from orion_integration.models import OrionNode
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


class NmapCertsData(BaseModel, models.Model):
    """
    SSL certificate data class

    #TODO: change all xml.dom objects to something readable by humans 
    """
    node_id = models.BigIntegerField(
        'orion node local id', blank=False, null=False, db_index=True,
        help_text='this is the primary keyof the orion node instance as'
        ' defined in the orion_integration application')
    addresses = models.CharField(max_length=100, blank=False, null=False)
    not_before = models.DateTimeField(
        'not before', db_index=True, null=False, blank=False,
        help_text='certificate not valid before this date')
    not_after = models.DateTimeField(
        'not after', db_index=True, null=False, blank=False,
        help_text='certificate not valid after this date')
    xml_data = models.TextField()
    common_name = models.CharField(
        'common name', db_index=True, max_length=100, blank=False, null=False,
        help_text='the CN part of an SSL certificate')
    organization_name = models.CharField(
        'organization', db_index=True, max_length=100, blank=True, null=True,
        help_text='the O part of the SSL certificate')
    country_name = models.CharField(max_length=100, blank=True, null=True)
    sig_algo = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    bits = models.CharField(max_length=100, blank=True, null=True)
    md5 = models.CharField(
        'md5', unique=True, db_index=True, max_length=100, blank=False,
        null=False)
    sha1 = models.CharField(
        'sha1', unique=True, db_index=True, max_length=100, blank=False,
        null=False)
    history = HistoricalRecords()

    @property
    @mark_safe
    def node_admin_url(self):
        """
        admin link to the Orion node where the certificate resides
        """
        orion_node = OrionNode.objects.filter(pk=self.node_id)
        if orion_node.exists():
            orion_node = orion_node.get()
            return '<a href="%s">%s on django</>' % (
                reverse('admin:orion_integration_orionnode_change',
                        args=(orion_node.id,)),
                orion_node.node_caption)

        return 'acquired outside the Orion infrastructure'

    @property
    @mark_safe
    def orion_node_url(self):
        """
        link to the Orion Node object on the Orion server
        """
        orion_node = OrionNode.objects.filter(pk=self.node_id)
        if orion_node.exists():
            orion_node = orion_node.values('node_caption', 'details_url')[0]
            return '<a href="%s%s">%s on Orion</>' % (
                settings.ORION_ENTITY_URL, orion_node.get('details_url'),
                orion_node.get('node_caption')
            )

        return 'acquired outside the Orion infrastructure'

    def __str__(self):
        return 'O: %s, CN: %s' % (self.organization_name, self.common_name)

    class Meta:
        verbose_name = 'SSL Certificate'
        verbose_name_plural = 'SSL Certificates'


class SslExpiresIn(NmapCertsData):
    """
    proxy model for valid SSL certificates sorted by expiration date
    """
    objects = ExpiresIn()

    class Meta:
        proxy = True
        verbose_name = 'Valid SSL Certificate'
        verbose_name_plural = 'Valid SSL Certificates by expiration date'


class SslHasExpired(NmapCertsData):
    """
    proxy model for valid SSL certificates sorted by expiration date
    """
    objects = ExpiredSince()

    class Meta:
        proxy = True
        verbose_name = 'SSL Certificate: expired'
        verbose_name_plural = 'SSL Certificates: expired'


class SslNotYetValid(NmapCertsData):
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
    headers = models.TextField(
        'data headers', blank=False, null=False,
        default='common_name,expires_in,not_before,not_after')

    def __str__(self):
        return self.subscription

    class Meta:
        app_label = 'ssl_cert_tracker'
