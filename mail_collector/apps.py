"""
django apps module for the mail_collector app

:module:    p_soc_auto.mail_collector.apps

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

Module used to register the :ref:`Mail Collector Application` with the
:ref:`SOC Automation Project`

"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MailCollectorConfig(AppConfig):
    """
    application class for :ref:`Mail Collector Application`
    """
    name = 'mail_collector'
    verbose_name = _(
        'PHSA Service Operations Center Exchange Monitoring Application')

    def ready(self):
        """
        documented solution for avoiding circular import errors when
        loading modules that use the django framework packages
        """
        # pylint: disable=import-outside-toplevel, unused-import
        import mail_collector.signals
