"""
.. _apps:

django apps module for the orion_flash app

:module:    p_soc_auto.orion_flash.apps

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class OrionFlashConfig(AppConfig):
    name = 'orion_flash'
    verbose_name = _(
        'PHSA Service Operations Center Orion Alerts')

    def ready(self):
        """
        place holder for weird imports
        """
        import orion_flash.signals  # @UnresolvedImport @UnusedImport
