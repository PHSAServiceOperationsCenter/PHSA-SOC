"""
.. _apps:

django apps module for the rules_engine app

:module:    p_soc_auto.rules_engine.apps

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    oct. 5, 2018
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class RulesEngineConfig(AppConfig):
    """
    application class for the rules_engine application
    """
    name = 'rules_engine'
    verbose_name = _(
        'PHSA Service Operations Center Rules Engine Application')

    def ready(self):
        """
        in case of circular imports or app not ready place imports
        in this method
        """
        pass
