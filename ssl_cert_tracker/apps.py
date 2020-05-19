"""
.. _ssl_apps:

:ref:`SSL Certificate Tracker Application` Definition
-----------------------------------------------------

:module:    ssl_certificates.apps

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SslCertificatesConfig(AppConfig):
    """
    `Django` application configuration class for the
    :ref:`SSL Certificate Tracker Application`

    See :attr:`p_soc_auto.settings.INSTALLED_APPS`.
    """
    name = 'ssl_cert_tracker'
    verbose_name = _(
        'PHSA Service Operations Center SSL Certificates Tracker')
