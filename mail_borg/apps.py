"""
.. _apps:

django apps module for the mail_collector app

:module:    p_soc_auto.mail_collector.apps

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    May 27, 2019

"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MailCollectorConfig(AppConfig):
    name = 'mail_collector'
    verbose_name = _(
        'PHSA Service Operations Center Exchange Monitoring Application')

    def ready(self):
        """
        place holder for weird imports
        """
        import citrus_borg.consumers
        # import mail_collector.signals
