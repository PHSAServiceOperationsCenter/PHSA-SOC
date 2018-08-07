"""
.. _apps:

django apps module for the ssl_certificates app

:module:    ssl_certificates.apps

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

"""
__updated__ = '2018_07_24'

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SslCertificatesConfig(AppConfig):
    name = 'ssl_cert_tracker'
    verbose_name = _('SSL Certificates Tracker')

    def ready(self):
        """
        the cleanest way to import modules from other
        """
        from base.models import BaseModel
