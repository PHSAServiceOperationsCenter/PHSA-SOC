"""
.. _apps:

django apps module for the uhuru app

:module:    uhuru.apps

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Nov. 23, 2018

"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UhuruConfig(AppConfig):
    name = 'uhuru'
    verbose_name = _('PHSA Service Operations Center Communications Station')

    def ready(self):
        """
        placeholder for django style imports
        """
        pass
