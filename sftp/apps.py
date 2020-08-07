"""
.. _base_apps:

sftp.apps
---------

This module contains the `Django` application configuration for sftp.


:module:    p_soc_auto.sftp.apps

:copyright:

    Copyright 2020 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class SftpConfig(AppConfig):
    """
    App class for the sftp application
    """
    name = 'sftp'
    verbose_name = _('SOC SFTP Application')
