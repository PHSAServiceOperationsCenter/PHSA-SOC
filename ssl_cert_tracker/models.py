"""
.. _models:

django models for the ssl_certificates app

:module:    ssl_certificates.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""
from django.db import models
from simple_history.models import HistoricalRecords

from p_soc_auto_base.models import BaseModel


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

    def __str__(self):
        return 'O: %s, CN: %s' % (self.organization_name, self.common_name)

    class Meta:
        verbose_name = 'SSL Certificate'
        verbose_name_plural = 'SSL Certificates'
