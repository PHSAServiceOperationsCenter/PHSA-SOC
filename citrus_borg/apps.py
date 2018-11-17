"""
.. _apps:

django apps module for the rules_engine app

:module:    p_soc_auto.orion_integration.apps

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    nov. 16, 2018

"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CitrusBorgConfig(AppConfig):
    name = 'citrus_borg'
    verbose_name = _(
        'PHSA Service Operations Center Citrix Logon Monitoring Application')

    def ready(self):
        """
        place holder for weird imports
        """
        pass
