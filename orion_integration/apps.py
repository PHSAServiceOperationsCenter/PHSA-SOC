"""
.. _apps:

django apps module for the orion integration app

:module:    p_soc_auto.orion_integration.apps

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca
"""
__updated__ = '2018_08_07'

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class OrionIntegrationConfig(AppConfig):
    """
    App class for the orion_integration django app
    """
    name = 'orion_integration'
    verbose_name = _(
        'PHSA Service Operations Center Orion Integration Application')
    
    def ready(self):
        """
        imports
        """
        from p_soc_auto_base.models import BaseModel
