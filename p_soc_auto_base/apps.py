"""
.. _base_apps:

p_soc_auto_base.apps module
---------------------------

This module contains the `Django` application configuration for the base app.


:module:    p_soc_auto.p_soc_auto_base.apps

:copyright:

    Copyright 2018 - 2020 Provincial Health Service Authority
    of British Columbia

"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PSocAutoBaseConfig(AppConfig):
    """
    App class for the base application
    """
    name = 'p_soc_auto_base'
    verbose_name = _('PHSA Service Operations Center Base Application')
