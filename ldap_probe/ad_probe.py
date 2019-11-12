"""
ldap_probe.ad_probe
-------------------

This module contains the `Active Directory
<https://en.wikipedia.org/wiki/Active_Directory>`__ client used by the
:ref:`Domain Controllers Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Nov. 12, 2019

"""
import logging

import ldap

from ldap_probe import exceptions, models
from p_soc_auto_base.utils import Timer


LOGGER = logging.getLogger('ldap_probe_log')


ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)


class _ADProbeElapsed():  # pylint: disable=too-few-public-methods
    """
    Private class for storing the various values of time elapsed while
    executing :class:`ldap.LDAPObject` methods of interest to us
    """

    def __init__(self):
        self.elapsed_initialize = None
        """elapsed time for :meth:`ldap.initialize`"""

        self.elapsed_bind = None
        """elapsed time for :meth:`ldap.LDAPObject.bind_s`"""

        self.elapsed_anon_bind = None
        """
        elapsed time for :meth:`ldap.LDAPObject.bind_s` when called
        anonymously
        """

        self.elapsed_read_root = None
        """elapsed time for :meth:`ldap.LDAPObject.read_rootdse_s`"""

        self.elapsed_search_ext = None
        """elapsed time for :meth:`ldap.LDAPObject.search_ext_s`"""


class ADProbe():
    """
    Utility class with timed methods that wrap around
    :class:`ldap.LDAPObject` methods of interest to us
    """

    def __init__(self, ad_controller=None, logger=LOGGER):
        self.logger = logger
        """private `logging.Logger` instance"""

        if ad_controller is None:
            raise exceptions.ADProbeControllerError(
                'One must provide a domain controller if one wants to'
                ' probe a domain controller'
            )

        if not isinstance(ad_controller, models.BaseADNode):
            raise TypeError(f'Invalid object type {type(ad_controller)!r}!')

        self.ad_controller = ad_controller
        """the AD controller object"""

        self.elapsed = _ADProbeElapsed()
        """keep track of all elapsed times for LDAP ops"""

        self.ldap_object = self.get_ldap_object()
        """the :class:`ldap.LDAPObject`"""

    def get_ldap_object(self):
        """
        initialize the :class:`ldap.LDAPObject`
        """
        with Timer() as timing:
            try:
                connection = ldap.initialize(self.ad_controller.get_node())
            except Exception as err:
                raise exceptions.ADProbeOperationalError(err)

        self.elapsed.elapsed_initialize = timing
        return connection

    def bind(self):
        """
        """

    def bind_anonym(self):
        """
        execute an anonymous :meth:`ldap.LDAPObject.bind_s` call and measure
        how long it took
        """
        with Timer() as timing:
            self.ldap_object.bind_s()

        self.elapsed.elapsed_anon_bind = timing
