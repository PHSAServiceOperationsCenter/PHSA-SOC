"""
.. _models:

django models for the ssl_certificates app

:module:    ssl_certificates.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

"""
from django.db import models
from django.utils.translation import gettext_lazy as _

from base.models import BaseModel


class Service(BaseModel, models.Model):
    """

    """
    service = models.CharField(
        _('service'), db_index=True, null=False, blank=False,
        max_length=64)
    host = models.CharField(
        _('host'), db_index=True, null=False, blank=False,
        max_length=255, help_text=_('this may end up being a foreign key'))
    port = models.CharField(
        _('port'), db_index=True, null=False, blank=False,
        max_length=5)

    class Meta:
        verbose_name = _('Service')
        verbose_name_plural = _('Services')
        unique_together = (('service', 'host', 'port',),)


class Certificate(BaseModel, models.Model):
    """
    certificates

    example:

        Subject: 
            commonName=www.paypal.com/
            organizationName=PayPal, Inc./
            stateOrProvinceName=California/countryName=US

        Subject Alternative Name: 
            DNS:history.paypal.com, DNS:t.paypal.com, 
            DNS:c.paypal.com, DNS:c6.paypal.com, 
            DNS:developer.paypal.com, DNS:p.paypal.com, 
            DNS:www.paypal.com

        Issuer: 
            commonName=Symantec Class 3 EV SSL CA - G3/
            organizationName=Symantec Corporation/countryName=US

        Public Key type: rsa

        Public Key bits: 2048

        Signature Algorithm: sha256WithRSAEncryption

        Not valid before: 2017-09-22T00:00:00

        Not valid after:  2019-10-30T23:59:59

        MD5:   cfce 8a0f 2e07 87ab 22bf 977f cb98 28aa

        _SHA-1: bb20 b03f fb93 e177 ff23 a743 8949 601a 41ae c61c
    """
    service = models.OneToOneField(Service)
    subject = models.TextField()
    subject_alt_name = models.TextField()
    issuer = models.TextField()
    pki_type = models.CharField(max_length=16)
    pki_bits = models.CharField(max_length=4)
    pki_algo = models.CharField(max_length=128)
    not_valid_before = models.DateTimeField()
    not_valid_after = models.DateTimeField()
    md5 = models.CharField(max_length=128)
    sha1 = models.CharField(max_length=256)
    
class Node(models.Model):
    dns=models.CharField(max_length=263)
    caption=models.CharField(max_length=263)

