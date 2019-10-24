"""
orion_integration.apps
----------------------

This module contains the `Django` application configuration for the
:ref:`Orion Integration Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Oct. 24, 2019
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrionIntegrationConfig(AppConfig):
    """
    Configuration class for the :ref:`Orion Integration Application`

    See `Configuring applications
    <https://docs.djangoproject.com/en/2.2/ref/applications/#projects-and-applications>`__
    in the `Django docs <https://docs.djangoproject.com/en/2.2/>`__
    """
    name = 'orion_integration'
    verbose_name = _(
        'PHSA Service Operations Center Orion Integration Application')

    def ready(self):
        """
        use this method for initialization purposes and to avoid `Django`
        circular import errors

        See `AppConfig.ready()
        <https://docs.djangoproject.com/en/2.2/ref/applications/#django.apps.AppConfig.ready>`__.
        """
        pass  # pylint: disable=unnecessary-pass
