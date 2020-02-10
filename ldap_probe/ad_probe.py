"""
ldap_probe.ad_probe
-------------------

This module contains the `Active Directory
<https://en.wikipedia.org/wiki/Active_Directory>`__ client used by the
:ref:`Active Directory Services Monitoring Application`.

The :mod:`python-ldap <ldap>` module is configured to use `TLS` by setting
the :attr:`ldap.OPT_X_TLS_REQUIRE_CERT` attribute but to not verify the `TLS`
certificate by setting the :attr:`ldap.OPT_X_TLS_NEVER` attribute.

As per the `python-ldap FAQ
<https://www.python-ldap.org/en/latest/faq.html#usage>`__ we are disabling
referrals on the :class:`ldap.LDAPObject` object because we are connecting
to a `Windows` `AD` controller.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
import logging

import ldap

from ldap_probe import models
from p_soc_auto_base.utils import Timer, diagnose_network_problem


LOG = logging.getLogger(__name__)
"""default :class:`logging.Logger` instance"""


ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_NEVER)


class ADProbe:
    """
    Class that wraps around :class:`ldap.LDAPObject` methods of interest
    to us and adds timing facilities to each of them
    """

    def __init__(self, ad_controller):
        """
        :class:`ADProbe` constructor
        """
        self.failed = False
        """
        track probe failure state

        It is easier to determine it here than to calculate it at
        the `Django model` level with a query against a text field.
        """

        self.abort = False
        """
        state variable

        If `True`, data collected by this :class:`ADProbe` instance will
        be made available for saving to the database but no other LDAP
        operations will be executed.
        """

        if not isinstance(ad_controller, models.BaseADNode):
            raise TypeError(f'Invalid object type {type(ad_controller)!r}!'
                            f' Abandoning the AD probe...')
        self.ad_controller = ad_controller
        """the AD controller object"""

        self.elapsed = {}
        """keep track of all elapsed times for LDAP ops"""

        self.ldap_object = None
        """the :class:`ldap.LDAPObject`"""

        self.errors = ''
        """store operational errors if any"""

        self.ad_response = None
        """did we get anything from the `AD` controller?"""

        self.get_ldap_object()


    @classmethod
    def probe(cls, ad_controller):
        """
        `class method
        <https://docs.python.org/3.6/library/functions.html#classmethod>`__
        that creates the :class:`ADProbe` instance and runs the `LDAP` probe
        in one shot
        """
        probe = cls(ad_controller)

        probe.bind_and_search()

        data = dict(probe.elapsed)

        data['ad_response'] = probe.ad_response
        data['errors'] = probe.errors
        data['failed'] = probe.failed

        return data

    def get_ldap_object(self):
        """
        initialize the :class:`ldap.LDAPObject`
        """
        LOG.debug('initialize ldap with %s', self.ad_controller.get_node())

        with Timer(use_duration=False) as timing:
            try:
                self.ldap_object = ldap.initialize(
                    f'ldaps://{self.ad_controller.get_node()}')
            except ldap.LDAPError as err:
                self.failed = True
                self._set_abort(
                    error_message=f'LDAP Initialization error: {err}')
                return

        self.elapsed['elapsed_initialize'] = timing.elapsed
        self.ldap_object.set_option(ldap.OPT_REFERRALS, ldap.OPT_OFF)

    def _set_abort(self, error_message=None):
        """
        set the abort flag and update the :attr:`errors` value
        """
        LOG.warning('aborting LDAP op for %s: %s',
                    self.ad_controller.get_node(), error_message)
        self.abort = True
        self.errors += f'\nAD probe aborted. {error_message}'

    def bind_and_search(self):
        """
        execute an :meth:`ldap.LDAPObject.bind_s` call
        and measure how long it took

        If :meth:`ldap.LDAPObject.bind_s` fails with
        :exc:`ldap.INVALID_CREDENTIALS`, we will fall back and try an
        anonymous bind with :meth:`bind_anon_and_read`
        """
        LOG.debug('trying bind ad search for %s with creds %s',
                  self.ad_controller.get_node(),
                  self.ad_controller.ldap_bind_cred)

        if self.abort:
            return

        with Timer(use_duration=False) as timing:
            try:
                self.ldap_object.bind_s(
                    self.ad_controller.ldap_bind_cred.username,
                    self.ad_controller.ldap_bind_cred.password)
            except ldap.SERVER_DOWN as err:
                self._diagnose_network(err)
                return
            except ldap.INVALID_CREDENTIALS as err:
                self._fallback(err)
                return
            except ldap.LDAPError as err:
                self.failed = True
                self._set_abort(error_message=f'Error: {err}.')
                return

        self.elapsed['elapsed_bind'] = timing.elapsed

        with Timer(use_duration=False) as timing:
            try:
                self.ad_response = self.ldap_object.search_ext_s(
                    self.ad_controller.ldap_bind_cred.ldap_search_base,
                    ldap.SCOPE_SUBTREE,
                    (f'(sAMAccountName='
                     f'{self.ad_controller.ldap_bind_cred.username})'))
            except ldap.REFERRAL as err:
                self.ad_response = (
                    'REFERRAL: %s'
                    % err.args[0].get("info")[len("Referral:\n"):])
                self.errors += (
                    f'Extended search error: {err}. The information is'
                    f' not available on the AD controller at'
                    f' {self.ad_controller.get_node()}')
            except ldap.LDAPError as err:
                self.failed = True
                self._set_abort(
                    error_message=f'Extended search error: {err}')
                return

        self.elapsed['elapsed_search_ext'] = timing.elapsed

    def _fallback(self, err):
        """
        try to fall back :meth:`bind_anon_and_read` if
        :meth:`bind_and_search` fails

        When :meth:`ldap.LDAPObject.bind_s` fails because the credentials are
        not known to the `AD` server, it is still possible to validate
        that said `AD` server is up if it will accept an anonymous bind.

        See `Common Active Directory Bind Errors
        <https://ldapwiki.com/wiki/Common%20Active%20Directory%20Bind%20Errors>`__
        for errors that will trigger a fall back.
        """
        self.errors += (f'\nTrying fall back from LDAP error'
                        f' {err.__class__.__name__}: {str(err)}.')
        self.bind_anon_and_read()

    def bind_anon_and_read(self):
        """
        execute an anonymous :meth:`ldap.LDAPObject.simple_bind_s` call
        and measure how long it took
        """
        LOG.debug('trying anonymous bind for %s',
                  self.ad_controller.get_node())
        if self.abort:
            return

        with Timer(use_duration=False) as timing:
            try:
                self.ldap_object.simple_bind_s()
            except ldap.SERVER_DOWN as err:
                self._diagnose_network(err)
                return
            except ldap.LDAPError as err:
                self.failed = True
                self._set_abort(error_message=f'Error: {err}')
                return

        self.elapsed['elapsed_anon_bind'] = timing.elapsed

        with Timer(use_duration=False) as timing:
            try:
                self.ad_response = self.ldap_object.read_rootdse_s()
            except ldap.LDAPError as err:
                self.failed = True
                self._set_abort(error_message=f'Error: {err}')
                return

        self.elapsed['elapsed_read_root'] = timing.elapsed

    def _diagnose_network(self, err):
        """
        try to figure why the `LDAP` probe has returned a network error

        Possible network errors:

        * :exc:`ldap.SERVER_DOWN`:

         {'desc': "Can't contact LDAP server", 'errno': 2,
         'info': 'No such file or directory'} may be a  bad dns name

        * :exc:`ldap.SERVER_DOWN`:

          {'desc': "Can't contact LDAP server", 'errno': 107,
          'info': 'Transport endpoint is not connected'} may be a bad port


        """
        self.failed = True
        self._set_abort(error_message=f'Network error: {err}')

        if err.args[0].get('errno') == 107:
            self.errors += (
                '\nBad network port or using ldaps://hostname for host'
                ' that only supports ldap')
        elif err.args[0].get('errno') == 2:
            self.errors += (
                f'\n'
                f'{diagnose_network_problem(self.ad_controller.get_node())}'
            )
        else:
            network_diagnostics = diagnose_network_problem(
                self.ad_controller.get_node())

            if not network_diagnostics[0]:
                self.errors += '\nUnknown network error'
            else:
                self.errors += network_diagnostics[1]
