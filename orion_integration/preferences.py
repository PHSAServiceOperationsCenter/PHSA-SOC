"""
orion_integration.preferences
-----------------------------

This module is used to provide run-time configurable settings.

See p_soc_auto_base.preferences for more info.

:copyright:

    Copyright 2021 Provincial Health Service Authority
    of British Columbia

"""
from django.conf import settings
from dynamic_preferences.preferences import Section

from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import (
    BooleanPreference, FloatPreference, IntPreference, LongStringPreference,
    StringPreference)

ORION_SERVER_CONN = Section(
    'orionserverconn',
    verbose_name=_('Orion Server Connection Settings').title())

ORION_FILTERS = Section(
    'orionfilters',
    verbose_name=_('Filters used for Orion REST queries').title())

ORION_PROBE_DEFAULTS = Section(
    'orionprobe',
    verbose_name=_('Filters used for Orion data probes').title())


@global_preferences_registry.register
class OrionServer(StringPreference):
    """
    Dynamic preference class for storing the host name of the `Orion` server

    :access_key: 'orionserverconn__orion_hostname'
    """
    section = ORION_SERVER_CONN
    name = 'orion_hostname'
    default = settings.ORION_HOSTNAME
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Orion Server Host Name or IP Address')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionProbeCSTOnly(BooleanPreference):
    """
    Dynamic preferences class controlling whether `NMAP` `SSL` probes are
    executed against `Cerner CST` `Orion` nodes or all `Orion` nodes

    This preference is used by the :ref:`Orion Integration Application`.

    :access_key: 'orionprobe__cerner_cst'
    """
    section = ORION_PROBE_DEFAULTS
    name = 'cerner_cst'
    default = True
    """default value for this dynamic preference"""
    required = False
    verbose_name = _('Only probe Cerner CST Orion nodes').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionProbeKnownSslOnly(BooleanPreference):
    """
    Dynamic preferences class controlling whether `NMAP` `SSL` probes are
    executed against `Orion` nodes tagged as `SSL` on the `Orion` server.

    This preference is used by the :ref:`Orion Integration Application`.

    :access_key: 'orionprobe__orion_ssl'
    """
    section = ORION_PROBE_DEFAULTS
    name = 'orion_ssl'
    default = False
    """default value for this dynamic preference"""
    required = False
    verbose_name = _(
        'Only probe Orion nodes known to serve applications over SSL').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionProbeServersOnly(BooleanPreference):
    """
    Dynamic preferences class controlling whether `NMAP` `SSL` probes are
    executed against `Orion` nodes tagged as `server nodes` on the `Orion`
    server.

    This preference is used by the :ref:`Orion Integration Application`.

    :access_key: 'orionprobe__servers_only'
    """
    section = ORION_PROBE_DEFAULTS
    name = 'servers_only'
    default = True
    """default value for this dynamic preference"""
    required = False
    verbose_name = _('Only probe Orion nodes categorized as servers').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionCernerCSTFilter(StringPreference):
    """
    Dynamic preferences class controlling the filter parameters used to extract
    `Cerner CST` `Orion` nodes

    This preference is used by the :ref:`Orion Integration Application`.

    :access_key: 'orionfilters__cerner_cst'
    """
    section = ORION_FILTERS
    name = 'cerner_cst'
    default = 'Cerner-CST'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Query Filter for Cerner CST Orion nodes').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionDomainControllerNodeFilter(StringPreference):
    """
    Dynamic preferences class controlling the filter parameters used to extract
    `Windows domain controller` `Orion` nodes

    This preference is used by the :ref:`Orion Integration Application`.

    :access_key: 'orionfilters__domaincontroller'
    """
    section = ORION_FILTERS
    name = 'domaincontroller'
    default = 'DomainController'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Query Filter for Windows domain controller Orion nodes').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionServerNodesFilter(StringPreference):
    """
    Dynamic preferences class controlling the filter parameters used to extract
    `server` `Orion` nodes

    This preference is used by the :ref:`Orion Integration Application`.

    :access_key: 'orionfilters__server_node'
    """
    section = ORION_FILTERS
    name = 'server_node'
    default = 'server'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Query Filter for Orion server nodes').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionAppSslFilter(StringPreference):
    """
    Dynamic preferences class controlling the filter parameters used to extract
    `SSL` `Orion` nodes

    This preference is used by the :ref:`Orion Integration Application`.

    :access_key: 'orionfilters__ssl_app'
    """
    section = ORION_FILTERS
    name = 'ssl_app'
    default = 'ssl'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Query Filter for Orion nodes known to run applications over SSL'
    ).title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionServerUrl(LongStringPreference):
    """
    Dynamic preferences class controlling the `Orion server` `URL`

    This preference is used by several applications in this project for
    calculating absolute `URL`s for `orion` nodes.

    :access_key: 'orionserverconn__orion_server_url'
    """
    section = ORION_SERVER_CONN
    name = 'orion_server_url'
    default = settings.ORION_ENTITY_URL
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Orion Server Root URL')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionServerRestUrl(LongStringPreference):
    """
    Dynamic preferences class controlling the `URL` for the `REST` `API`
    provided by the `Orion server`

    This preference is used by several applications in this project to query
    the `Orion` server for data about `Orion` nodes.

    :access_key: 'orionserverconn__orion_rest_url'
    """
    section = ORION_SERVER_CONN
    name = 'orion_rest_url'
    default = settings.ORION_URL
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Orion Server REST API root URL')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionServerUser(StringPreference):
    """
    Dynamic preference class for storing the username used for accessing the
    `REST` `API` provided by the `Orion` server

    :access_key: 'orionserverconn__orion_user'
    """
    section = ORION_SERVER_CONN
    name = 'orion_user'
    default = settings.ORION_USER
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Orion Server User Name')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionServerPassword(StringPreference):
    """
    Dynamic preference class for storing the password used for accessing the
    `REST` `API` provided by the `Orion` server

    :access_key: 'orionserverconn__orion_password'
    """
    section = ORION_SERVER_CONN
    name = 'orion_password'
    default = settings.ORION_PASSWORD
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Orion Server Password')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionServerAcceptUnsignedCertificate(BooleanPreference):
    """
    Dynamic preference class controlling whether the modules in this project
    will verify the `SSL server certificate` of the `Orion` server when `REST`
    calls are  made over `HTTPS`

    :access_key: 'orionserverconn__orion_verify_ssl_cert'
    """
    section = ORION_SERVER_CONN
    name = 'orion_verify_ssl_cert'
    default = settings.ORION_VERIFY_SSL_CERT
    """default value for this dynamic preference"""
    required = False
    verbose_name = _('Ignore unsigned SSL certificate on the Orion server')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionServerConnectionTimeout(FloatPreference):
    """
    Dynamic preferences class used for storing the connection timeout used
    by `REST` calls to the `Orion` server

    :access_key: 'orionserverconn__orion_conn_timeout'
    """
    section = ORION_SERVER_CONN
    name = 'orion_conn_timeout'
    default = settings.ORION_TIMEOUT[0]
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Orion Server Connection Timeout')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionServerReadTimeout(FloatPreference):
    """
    Dynamic preferences class used for storing the read timeout used
    by `REST` calls to the `Orion` server

    :access_key: 'orionserverconn__orion_read_timeout'
    """
    section = ORION_SERVER_CONN
    name = 'orion_read_timeout'
    default = settings.ORION_TIMEOUT[1]
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Orion Server Read Timeout')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionServerRetry(IntPreference):
    """
    Dynamic preferences class used for storing the number of retries used
    by `REST` calls to the `Orion` server

    :access_key: 'orionserverconn__orion_retry'
    """
    section = ORION_SERVER_CONN
    name = 'orion_retry'
    default = settings.ORION_RETRY
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Orion Server Connection Retries')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class OrionServerRetryBackoff(FloatPreference):
    """
    Dynamic preferences class used for storing the retry back-off factor used
    by `REST` calls to the `Orion` server

    :access_key: 'orionserverconn__orion_backoff_factor'
    """
    section = ORION_SERVER_CONN
    name = 'orion_backoff_factor'
    default = settings.ORION_BACKOFF_FACTOR
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Orion Server Retry Backoff Factor')
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "See 'backoff_factor' at <a href={}>{}</a>",
        'https://urllib3.readthedocs.io/en/latest/reference/'
        'urllib3.util.html#module-urllib3.util.retry',
        _('Retry connection backoff factor'))
