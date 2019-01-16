"""
.. _apps:

django apps module for the citrus_borg app

:module:    p_soc_auto.citrus_borg.apps

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Jan. 15, 2019

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
        import citrus_borg.consumers
