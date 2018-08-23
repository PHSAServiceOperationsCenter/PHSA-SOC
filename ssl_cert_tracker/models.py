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

class TestCertsData(models.Model):
    """TestCertsData. Model struture for NMap result response. """
    ip_value = models.CharField(max_length=100, blank=True, null=True)
    valid_start = models.DateTimeField(null=True, blank=True)
    valid_end = models.DateTimeField(null=True, blank=True)
    xmldata = models.TextField(verbose_name='??', null=True,)
    status = models.CharField(max_length=100, blank=True, null=True)
    hostname =  models.CharField(max_length=100, blank=True, null=True)
    commonName =  models.CharField(max_length=100, blank=True, null=True)
    organizationName =  models.CharField(max_length=100, blank=True, null=True)
    countryName =  models.CharField(max_length=100, blank=True, null=True)
    sig_algo =  models.CharField(max_length=100, blank=True, null=True)
    name =  models.CharField(max_length=100, blank=True, null=True)
    bits =  models.CharField(max_length=100, blank=True, null=True)
    md5 =  models.CharField(max_length=100, blank=True, null=True)
    sha1 =  models.CharField(max_length=100, blank=True, null=True)
    orion_id =  models.CharField(max_length=100, blank=True, null=True)