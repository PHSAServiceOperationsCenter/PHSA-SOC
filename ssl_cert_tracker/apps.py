"""
.. _apps:

django apps module for the ssl_certificates app

:module:    ssl_certificates.apps

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Jul. 24, 2018

"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SslCertificatesConfig(AppConfig):
    """
    App class for the SSL Certificates Tracker application
    """
    name = 'ssl_cert_tracker'
    verbose_name = _('SSL Certificates Tracker')

    def ready(self):
        """
        the cleanest way to import modules from other
        to avoid circular import errors django provides this method that
        guarantees that imports will only happen after all the applications
        have been loaded
        """
        pass
