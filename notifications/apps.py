"""
.. _apps:

django apps module for the orion integration app

:module:    p_soc_auto.notifications.apps

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

:updated:    Sep. 20, 2018
"""
from django.apps import AppConfig
from django.db.models.signals import post_save
from django.utils.translation import gettext_lazy as _


class NotificationsConfig(AppConfig):
    """
    App class for the notifications django app
    """
    name = 'notifications'
    verbose_name = _(
        'PHSA Service notifications Application')

    def ready(self):
        """
        in case of circular imports or app not ready place imports
        in this method
        """
        pass
