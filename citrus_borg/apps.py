"""
.. _citrus_apps:

citrus_borg.apps module
-----------------------

This module contains the `Django` application configuration for the
:ref:`Citrus Borg Application`.


:module:    p_soc_auto.citrus_borg.apps

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CitrusBorgConfig(AppConfig):
    """
    Configuration class for the :ref:`Citrus Borg Application`

    See `Configuring applications
    <https://docs.djangoproject.com/en/2.2/ref/applications/#projects-and-applications>`__
    in the `Django docs <https://docs.djangoproject.com/en/2.2/>`__
    """
    name = 'citrus_borg'
    verbose_name = _(
        'PHSA Service Operations Center Citrix Logon Monitoring Application')

    def ready(self):
        """
        use this method for initialization purposes and to avoid `Django`
        circular import errors

        See `AppConfig.ready()
        <https://docs.djangoproject.com/en/2.2/ref/applications/#django.apps.AppConfig.ready>`__.
        """
        # These imports are required for Django to set up correctly.
        # pylint: disable=import-outside-toplevel, unused-import
        import citrus_borg.consumers
        import citrus_borg.signals
