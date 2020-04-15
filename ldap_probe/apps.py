"""
ldap_probe.apps
----------------------

This module contains the `Django` application configuration for the
:ref:`Active Directory Services Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class LdapProbeConfig(AppConfig):
    """
    Configuration class for the :ref:`Active Directory Services Monitoring
    Application`

    See `Configuring applications
    <https://docs.djangoproject.com/en/2.2/ref/applications/#projects-and-applications>`__
    in the `Django docs <https://docs.djangoproject.com/en/2.2/>`__
    """
    name = 'ldap_probe'
    verbose_name = _(
        'PHSA Service Operations Center Domain Controllers Monitoring'
        ' Application')

    def ready(self):
        """
        use this method for initialization purposes and to avoid `Django`
        circular import errors

        See `AppConfig.ready()
        <https://docs.djangoproject.com/en/2.2/ref/applications/#django.apps.AppConfig.ready>`__.
        """
        import ldap_probe.signals  # pylint: disable=import-outside-toplevel,unused-import
