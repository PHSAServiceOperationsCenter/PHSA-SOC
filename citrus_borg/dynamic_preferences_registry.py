"""
citrus_borg.dynamic_preferences_registry
----------------------------------------

This module is used to provide run-time configurable settings.

Although it is defined as part of the :ref:`Citrus Borg Application`, it
is shared across all the applications in the :ref:`SOC Automation Project`.

Each class in the module is a dynamic preference and each dynamic preference
can be configured via the `Global preferences admin interface
<../../../admin/dynamic_preferences/globalpreferencemodel/>`_ using the value
of the ``verbose_name`` attribute of the class.

To access the value of a given dynamic setting, use the :func:`get_preference`
function. For example:

.. ipython::

    In [1]: from citrus_borg.dynamic_preferences_registry import get_preference

    In [2]: get_preference('exchange__report_interval')
    Out[2]: datetime.timedelta(1, 43200)

    In [3]:

:copyright:

    Copyright 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
# TODO move each section to its own file

import decimal

from django.conf import settings
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import (
    BooleanPreference, StringPreference, DurationPreference, IntPreference,
    LongStringPreference, FloatPreference, DecimalPreference,
)


CITRUS_BORG_COMMON = Section(
    'citrusborgcommon', verbose_name=_('citrus borg common settings').title())

CITRUS_BORG_EVENTS = Section(
    'citrusborgevents', verbose_name=_('citrus borg event settings').title())

CITRUS_BORG_NODE = Section(
    'citrusborgnode', verbose_name=_('Citrus Borg Node settings').title())

CITRUS_BORG_UX = Section(
    'citrusborgux',
    verbose_name=_('Citrus Borg User Experience settings').title())

CITRUS_BORG_LOGON = Section(
    'citrusborglogon',
    verbose_name=_('Citrus Borg Citrix Logon settings').title())

ORION_SERVER_CONN = Section(
    'orionserverconn',
    verbose_name=_('Orion Server Connection Settings').title())

ORION_FILTERS = Section(
    'orionfilters',
    verbose_name=_('Filters used for Orion REST queries').title())

ORION_PROBE_DEFAULTS = Section(
    'orionprobe',
    verbose_name=_('Filters used for Orion data probes').title())

SFTP_DEFAULTS = Section(
    'sftp',
    verbose_name=_('Settings used to interact with the sftp server').title())

EMAIL_PREFS = Section('emailprefs', verbose_name=_(
    'Email preferences').title())

EXCHANGE = Section('exchange',
                   verbose_name=_(
                       'Options for the PHSA Service Operations Center'
                       ' Exchange Monitoring Application'))

LDAP_PROBE = Section('ldapprobe',
                     verbose_name=_(
                         'Options for the PHSA Service Operations Center'
                         ' Active Directory Services Monitoring Application'))
"""
dynamic user preferences section for the :ref:`Active Directory Services
Monitoring Application`
"""

COMMON_ALERT_ARGS = Section(
    'commonalertargs',
    verbose_name=_(
        'Common Args for Alerts Raised by the PHSA'
        ' Service Operations Center Automation Server'))
"""
dynamic user preferences section for preferences common to all applications
in the :ref:`SOC Automation Project`
"""


# The way dynamic preferences are set-up in Django we need to have these data
# classes without public methods
# pylint: disable=too-few-public-methods


@global_preferences_registry.register
class AlertArgsErrorLevel(StringPreference):
    """
    Dynamic preferences class controlling the value used for indicating
    if an alert is considered an `ERROR` alert

    This preference should be shared among :ref:`SOC Automation Server`
    applications.

    :access_key: 'commonalertargs__error_level'

    .. todo::

        Refactor all uses of alert and report levels to use this, and related,
        dynamic preferences.

    """
    section = COMMON_ALERT_ARGS
    name = 'error_level'
    default = 'ERROR'
    """default setting value"""
    required = True
    verbose_name = _('Tag for identifying ERROR alerts and/or reports')
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class AlertArgsWarnLevel(StringPreference):
    """
    Dynamic preferences class controlling the value used for indicating
    if an alert is considered a `WARNING` alert

    This preference should be shared among :ref:`SOC Automation Server`
    applications.

    :access_key: 'commonalertargs__warn_level'

    """
    section = COMMON_ALERT_ARGS
    name = 'warn_level'
    default = 'WARNING'
    """default setting value"""
    required = True
    verbose_name = _('Tag for identifying WARNING alerts and/or reports')
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class AlertArgsInfoLevel(StringPreference):
    """
    Dynamic preferences class controlling the value used for indicating
    if an alert is considered an `INFO` alert

    This preference should be shared among :ref:`SOC Automation Server`
    applications.

    :access_key: 'commonalertargs__info_level'

    """
    section = COMMON_ALERT_ARGS
    name = 'info_level'
    default = 'INFO'
    """default setting value"""
    required = True
    verbose_name = _('Tag for identifying INFO alerts and/or reports')
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class AlertArgsCriticalLevel(StringPreference):
    """
    Dynamic preferences class controlling the value used for indicating
    if an alert is considered an `CRITICAL` alert

    This preference should be shared among :ref:`SOC Automation Server`
    applications.

    :access_key: 'commonalertargs__crit_level'

    """
    section = COMMON_ALERT_ARGS
    name = 'crit_level'
    default = 'CRITICAL'
    """default setting value"""
    required = True
    verbose_name = _('Tag for identifying CRITICAL alerts and/or reports')
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class ExchangeExpireEvents(DurationPreference):
    """
    Dynamic preferences class controlling how old an event collected by the
    :ref:`Mail Collector Application` must be before it will be marked
    as expired

    :access_key: 'exchange__expire_events`
    """
    section = EXCHANGE
    name = 'expire_events'
    default = timezone.timedelta(hours=36)
    """default setting value"""
    required = True
    verbose_name = _('Exchange events older than')
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class ExchangeReportingInterval(DurationPreference):
    """
    Dynamic preferences class controlling the time interval used by the
    :ref:`Mail Collector Application` for generating reports

    :access_key: 'exchange__report_interval'
    """
    section = EXCHANGE
    name = 'report_interval'
    default = timezone.timedelta(hours=12)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange reporting interval')
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class ExchangeReportErrorLevel(StringPreference):
    """
    Dynamic preferences class controlling the error level used by the
    :ref:`Mail Collector Application` when generating reports

    :access_key: 'exchange__report_level'
    """
    section = EXCHANGE
    name = 'report_level'
    default = 'INFO'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Error level for all Exchange reports')
    """verbose name of this dynamic preference"""
    help_text = format_html(
        "{}", _('a report does not really have an error level but we need'
                ' a value here than can be empty, i.e. no level in order'
                ' to reuse existing mail templates'))


@global_preferences_registry.register
class ExchangeDeleteExpired(BooleanPreference):
    """
    Dynamic preferences class controlling whether expired event collected by
    the :ref:`Mail Collector Application` will be deleted

    :access_key: `exchange__delete_expired`
    """
    section = EXCHANGE
    name = 'delete_expired'
    default = True
    """default value for this dynamic preference"""
    required = False
    verbose_name = _('Delete expired Exchange events')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class ExchangeSendEmptyAlerts(BooleanPreference):
    """
    Dynamic preferences class controlling whether emails are being sent
    by the :ref:`Mail Collector Application` when an alert is not being
    raised. This the opposite of the `No news is good news
    <https://www.phrases.org.uk/bulletin_board/45/messages/366.html>`_ phrase

    :access_key: 'exchange__empty_alerts'
    """
    section = EXCHANGE
    name = 'empty_alerts'
    default = False
    """default value for this dynamic preference"""
    required = False
    verbose_name = _('Always Send Email Alerts')
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('send email notifications even when there are no alerts'))


@global_preferences_registry.register
class ExchangeDefaultErrorLevel(StringPreference):
    """
    Dynamic preferences class controlling the error level used by the
    :ref:`Mail Collector Application` when sending alerts for which no
    error level was specified

    :access_key: 'exchange__default_level`
    """
    section = EXCHANGE
    name = 'default_level'
    default = 'WARNING'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Default error level for Exchange alerts')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class ExchangeEventSource(StringPreference):
    """
    Dynamic preferences class that provides the key used by the
    :ref:`Mail Collector Application` data collection to identify
    events of interest

    :access_key: 'exchange__source'
    """
    section = EXCHANGE
    name = 'source'
    default = 'BorgExchangeMonitor'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Windows Logs Source for Exchange Monitoring Events ')
    """verbose name for this dynamic preference"""
    help_text = _(
        'This is a list of values. Use "," to separate the list items')


@global_preferences_registry.register
class ExchangeServerWarn(DurationPreference):
    """
    Dynamic preferences class controlling how long the
    :ref:`Mail Collector Application` will wait before raising a warning
    about an Exchange entity not providing Exchange services

    :access_key: 'exchange__server_warn'
    """
    section = EXCHANGE
    name = 'server_warn'
    default = timezone.timedelta(hours=2)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange server warnings after').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('raise warning about an Exchange server if it has not been'
                ' seen for longer than this time period'))


@global_preferences_registry.register
class ExchangeServerError(DurationPreference):
    """
    Dynamic preferences class controlling how long the
    :ref:`Mail Collector Application` will wait before raising an error
    about an Exchange entity not providing Exchange services

    :access_key: 'exchange__server_error'
    """
    section = EXCHANGE
    name = 'server_error'
    default = timezone.timedelta(hours=6)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange server errors after').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('raise error about an Exchange server if it has not been'
                ' seen for longer than this time period'))


@global_preferences_registry.register
class ExchangeDeadBotWarn(DurationPreference):
    """
    Dynamic preferences class controlling how long the
    :ref:`Mail Collector Application` will wait before raising a warning
    about an Exchange monitoring bot not sending any Exchange events

    :access_key: 'exchange__bot_warn'
    """
    section = EXCHANGE
    name = 'bot_warn'
    default = timezone.timedelta(hours=2)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange client bot warnings after').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('raise warning about an Exchange client bot if it has not been'
                ' seen for longer than this time period'))


@global_preferences_registry.register
class ExchangeNilDuration(DurationPreference):
    """
    Dynamic preferences class providing a 0 duration for internal use
    within the :ref:`Mail Collector Application`

    :access_key: 'exchange__nil_duration'

    """
    section = EXCHANGE
    name = 'nil_duration'
    default = timezone.timedelta(hours=0)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('nil duration').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('some filters will not work if there is no time interval'
                ' baked in. if we want to reuse these filters without'
                ' worrying about the time interval we can use this'))


@global_preferences_registry.register
class ExchangeDeadBotError(DurationPreference):
    """
    Dynamic preferences class controlling how long the
    :ref:`Mail Collector Application` will wait before raising an error
    about an Exchange monitoring bot not sending any Exchange events

    :access_key: 'exchange__bot_error'
    """
    section = EXCHANGE
    name = 'bot_error'
    default = timezone.timedelta(hours=6)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange client bot errors after').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('raise error about an Exchange client bot if it has not been'
                ' seen for longer than this time period'))


@global_preferences_registry.register
class ExchangeDefaultError(DurationPreference):
    """
    Dynamic preferences class controlling how long the
    :ref:`Mail Collector Application` will wait before raising an error
    about unspecified items

    :access_key: 'exchange__bot_error'

    """
    section = EXCHANGE
    name = 'default_error'
    default = timezone.timedelta(hours=2)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange errors after (default)').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('fallback error configuration for all exchange entities'))


@global_preferences_registry.register
class CitrusBorgEventSource(StringPreference):
    """
    Dynamic preferences class controlling the `Application` property of the
    `Windows` log events sent by `Citrix` monitoring bots

    This preference is used in the :ref:`Citrus Borg Application`.

    :access_key: 'citrusborgevents__source'
    """
    section = CITRUS_BORG_EVENTS
    name = 'source'
    default = 'ControlUp Logon Monitor'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Windows Logs Source for Citrix Events ').title()
    """verbose name for this dynamic preference"""
    help_text = _(
        'This is a list of values. Use "," to separate the list items')


@global_preferences_registry.register
class EmailFromWhenDebug(StringPreference):
    """
    Dynamic preferences class controlling the `FROM:` email address used by the
    :class:`ssl_cert_tracker.lib.Email` class when sending emails in `DEBUG`
    mode

    This preference applies to all the applications in the project.

    :access_key: 'emailprefs__from_email'
    """
    section = EMAIL_PREFS
    name = 'from_email'
    default = 'daniel.busto@phsa.ca'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('originating email address when in DEBUG mode').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class EmailToWhenDebug(StringPreference):
    """
    Dynamic preferences class controlling the `TO:` email address used by the
    :class:`ssl_cert_tracker.lib.Email` class when sending emails in `DEBUG`
    mode

    This preference applies to all the applications in the project.

    :access_key: 'emailprefs__to_emails'
    """
    section = EMAIL_PREFS
    name = 'to_emails'
    default = 'daniel.busto@phsa.ca,james.reilly@phsa.ca'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('destination email addresses when in DEBUG mode').title()
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


@global_preferences_registry.register
class ServiceUser(StringPreference):
    """
    Dynamic preferences class used for storing the name of the service user
    that the background processes in the :ref:`Citrus Borg Application` are
    using when accessing the database

    :access_key: 'citrusborgcommon__service_user'
    """
    section = CITRUS_BORG_COMMON
    name = 'service_user'
    default = settings.CITRUS_BORG_SERVICE_USER
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('citrus borg service user').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('default django user instance for background server processes.'),
        _('will be created automatically if it does not exist already'))


@global_preferences_registry.register
class SendNoNews(BooleanPreference):
    """
    Dynamic preferences class used for controlling whether the :ref:`Citrus
    Borg Application` will send email notifications when no alert conditions
    are detected

    :access_key: 'citrusborgcommon__send_no_news'
    """
    section = CITRUS_BORG_COMMON
    name = 'send_no_news'
    default = settings.CITRUS_BORG_NO_NEWS_IS_GOOD_NEWS
    """default value for this dynamic preference"""
    required = False
    verbose_name = _("do not send empty citrix alert emails").title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('by default the application sends alert emails even if there is no'
          ' alert.'),
        _('enable this setting to only send alert emails if alerts have'
          ' occurred'))


@global_preferences_registry.register
class DeadAfter(DurationPreference):
    """
    Dynamic preferences class storing the interval used as threshold for
    raising alerts about `Citrix` entities that have not been seen by the
    system

    If a `Citrix` entity has not been observed in a `Windows` log event
    for a period longer than this interval, the alert will be raised.

    :access_key: 'citrusborgcommon__dead_after'
    """
    section = CITRUS_BORG_COMMON
    name = 'dead_after'
    default = settings.CITRUS_BORG_IGNORE_EVENTS_OLDER_THAN
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('dead if not seen for more than').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('report a site, bot, or session host as dead if events mentioning'),
        _('them have not been received for more than this time period'))


@global_preferences_registry.register
class IgnoreEvents(DurationPreference):
    """
    Dynamic preferences class storing the cutoff age for `Citrix` events

    Events older than the cuttoff will not considered when evaluating alerts or
    generating report.

    :access_key: 'citrusborgevents__ignore_events_older_than'
    """
    section = CITRUS_BORG_EVENTS
    name = 'ignore_events_older_than'
    default = settings.CITRUS_BORG_IGNORE_EVENTS_OLDER_THAN
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('ignore events created older than').title()
    """verbose name for this dynamic preference"""
    help_text = _(
        'events older than this value will not be used for any analysis')


@global_preferences_registry.register
class ExpireEvents(DurationPreference):
    """
    Dynamic preferences class controlling how old `Citrix` events are before
    they are marked as `expired`

    :access_key: 'citrusborgevents__expire_events_older_than'
    """
    section = CITRUS_BORG_EVENTS
    name = 'expire_events_older_than'
    default = settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('mark events as expired if older than').title()
    """verbose name for this dynamic preference"""
    help_text = _(
        'events older than this value will be marked as expired')


@global_preferences_registry.register
class DeleteExpireEvents(BooleanPreference):
    """
    Dynamic preferences class controlling whether `expired` `Citrix` events
    will be deleted

    :access_key: 'citrusborgevents__delete_expired_events'
    """
    section = CITRUS_BORG_EVENTS
    name = 'delete_expired_events'
    default = settings.CITRUS_BORG_DELETE_EXPIRED
    """default value for this dynamic preference"""
    required = False
    verbose_name = _('delete expired events').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class UxAlertThreshold(DurationPreference):
    """
    Dynamic preferences class storing the threshold used for evaluating
    `Citrix` response times

    :access_key: 'citrusborgux__ux_alert_threshold'
    """
    section = CITRUS_BORG_UX
    name = 'ux_alert_threshold'
    default = settings.CITRUS_BORG_UX_ALERT_THRESHOLD
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'maximum acceptable response time for citrix events').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('raise a user experience degraded alert if the response time for'),
        _('any monitored citrix event is higher than this value'))


@global_preferences_registry.register
class UxAlertInterval(DurationPreference):
    """
    Dynamic preferences class storing the sampling interval used for evaluating
    alerts about `Citrix` response times

    :access_key: 'citrusbirgux__ux_alert_interval'
    """
    section = CITRUS_BORG_UX
    name = 'ux_alert_interval'
    default = settings.CITRUS_BORG_UX_ALERT_INTERVAL
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('alert monitoring interval for citrix events').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('measure the user experience response time for citrix events'),
        _('once per this time interval for every site/bot combination'))


@global_preferences_registry.register
class UxReportingPeriod(DurationPreference):
    """
    Dynamic preferences class used for storing the interval used when
    generating reports about `Citrix` response times

    :access_key: 'citrusborgux__ux_reporting_period'
    """
    section = CITRUS_BORG_UX
    name = 'ux_reporting_period'
    default = settings.CITRUS_BORG_SITE_UX_REPORTING_PERIOD
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('user experience reporting period').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('email a report with the citrix event response time averaged'),
        _('per hour for each site, bot comination over this time interval'))


@global_preferences_registry.register
class ClusterEventIds(StringPreference):
    """
    Dynamic preference used for storing the ids that are considered pertinent to
    recognizing clusters of citrix events

    :access_key: 'citrusborgux__cluster_event_ids
    """
    section = CITRUS_BORG_UX
    name = 'cluster_event_ids'
    default = '1006,1007,1016,1017'
    required = True
    verbose_name = _('ids of events to consider when searching for clusters')\
        .title()
    help_text = format_html(
        '{}<br>{}',
        _('events with ids on this list will be counted when'),
        _('looking for event clusters'))


@global_preferences_registry.register
class ClusterLength(DurationPreference):
    """
    Dynamic preference used for storing the length of time to consider when
    searching for clusters

    :access_key: 'citrusborgux__cluster_length
    """
    section = CITRUS_BORG_UX
    name = 'cluster_length'
    default = timezone.timedelta(minutes=5)
    required = True
    verbose_name = _('amount of time to consider when searching for clusters')\
        .title()
    help_text = format_html(
        '{}<br>{}',
        _('when a failure occurs any events within this duration in the'),
        _('past will be considered when looking for clusters'))


@global_preferences_registry.register
class ClusterSize(IntPreference):
    """
    Dynamic preference used for storing the number of failures that makes a
    cluster

    :access_key: 'citrusborgux__cluster_size
    """
    section = CITRUS_BORG_UX
    name = 'cluster_size'
    default = 5
    required = True
    verbose_name = _('number of failures that makes a cluster').title()
    help_text = format_html(
        '{}<br>{}',
        _('if more than this many failures have occurred recently'),
        _('than a cluster alert will be sent'))


@global_preferences_registry.register
class BackoffTime(DurationPreference):
    """
    Dynamic preference used for storing the time period to consider to mute
    new cluster alerts

    :access_key: 'citrusborgux__backoff_time
    """
    section = CITRUS_BORG_UX
    name = 'backoff_time'
    default = timezone.timedelta(hours=1)
    required = True
    verbose_name = _(
        'amount of time to consider when considering whether to send page'
    ).title()
    help_text = format_html(
        '{}<br>{}',
        _('when a failure occurs any cluster within this duration is counted'),
        _('towards the backoff limit'))


@global_preferences_registry.register
class BackoffLimit(IntPreference):
    """
    Dynamic preference used for storing the time period to consider to mute
    new cluster alerts

    :access_key: 'citrusborgux__backoff_limit
    """
    section = CITRUS_BORG_UX
    name = 'backoff_limit'
    default = 3
    required = True
    verbose_name = _(
        'numbers of clusters after which we will not send pages'
    ).title()
    help_text = format_html(
        '{}<br>{}',
        _('when a failure occurs any if there are more clusters than this in'),
        _('the backoff time we will not send out a page'))


@global_preferences_registry.register
class NodeForgottenAfter(DurationPreference):
    """
    Dynamic preferences class used for storing the interval used when
    generating reports about `Citrix` entities that have not been seen for a
    while

    :access_key: 'citruxborgnode__node_forgotten_after'
    """
    section = CITRUS_BORG_NODE
    name = 'node_forgotten_after'
    default = settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('reporting period for dead nodes').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('reports about dead bots, site, or session hosts are based'),
        _('on this period'))


@global_preferences_registry.register
class BotAlertAfter(DurationPreference):
    """
    Dynamic preferences class used for storing the threshold for alerts about
    bots not sending any `Citrix` events

    :access_key: 'citrusborgnode__dead_bot_after'
    """
    section = CITRUS_BORG_NODE
    name = 'dead_bot_after'
    default = settings.CITRUS_BORG_DEAD_BOT_AFTER
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('bot not seen alert threshold').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('raise an alert if a bot has not sent any events for a period'),
        _('longer than this time interval'))


@global_preferences_registry.register
class SiteAlertAfter(DurationPreference):
    """
    Dynamic preferences class used for storing the threshold for alerts about
    remote sites not sending any `Citrix` events

    :access_key: 'citrusborgnode__dead_site_after'
    """
    section = CITRUS_BORG_NODE
    name = 'dead_site_after'
    default = settings.CITRUS_BORG_DEAD_SITE_AFTER
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('site not seen alert threshold').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('raise an alert if none of the bots on a site has sent any events'),
        _('for a period longer than this time interval'))


@global_preferences_registry.register
class SessionHostAlertAfter(DurationPreference):
    """
    Dynamic preferences class used for storing the threshold for alerts about
    `Citrix` session hosts not servicing requests
    """
    section = CITRUS_BORG_NODE
    name = 'dead_session_host_after'
    default = settings.CITRUS_BORG_DEAD_BROKER_AFTER
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('session host not seen alert threshold').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}<br>{}<br>{}",
        _('raise an alert if a known session host has not served any Citrix'),
        _('requests for a period longer than this time interval.'),
        _('note that session hosts are owned by Cerner and these alerts are'),
        _('mostly informative in nature'))


@global_preferences_registry.register
class FailedLogonAlertInterval(DurationPreference):
    """
    Dynamic preferences class storing the evaluation interval for alerts about
    failed logon events

    :access_key: 'citrusborglogon__logon_alert_after'
    """
    section = CITRUS_BORG_LOGON
    name = 'logon_alert_after'
    default = settings.CITRUS_BORG_FAILED_LOGON_ALERT_INTERVAL
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('failed logons alert interval').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('interval at which to verify sites and bots for failed logon'),
        _('events'))


@global_preferences_registry.register
class FailedLogonAlertThreshold(IntPreference):
    """
    Dynamic preferences class controlling the alert threshold for failed
    `Citrix` logon events

    This preference is used if one want to ignore random, unrepeated failed
    `Citrix` logon events.

    :access_key: 'citrusborglogon__logon_alert_threshold'
    """
    section = CITRUS_BORG_LOGON
    name = 'logon_alert_threshold'
    required = True
    default = settings.CITRUS_BORG_FAILED_LOGON_ALERT_THRESHOLD
    """default value for this dynamic preference"""
    verbose_name = _('failed logon events count alert threshold').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('how many times does a failed logon happen in a given interval'),
        _('before an alert is raised'))


@global_preferences_registry.register
class LogonReportsInterval(DurationPreference):
    """
    Dynamic preferences class controlling the reporting interval for `Citrix`
    logon events

    :access_key: 'citrusborglogon__logon_report_period'
    """
    section = CITRUS_BORG_LOGON
    name = 'logon_report_period'
    default = settings.CITRUS_BORG_FAILED_LOGONS_PERIOD
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('logon events reporting period').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('logon reports are calculated, created, and sent over this'),
        _('time interval'))


@global_preferences_registry.register
class LdapSearchBaseDNDefault(StringPreference):
    """
    Dynamic preferences class controlling the default value for the
    base DN argument used by LDAP search functions

    For example, an LDAP search for the `LoginPI01` account can  be initiated
    from `'dc=vch,dc=ca'`.

    :access_key: 'ldapprobe__search_dn_default'
    """
    section = LDAP_PROBE
    name = 'search_dn_default'
    default = 'dc=vch,dc=ca'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Default search base DN').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('Default value for the base DN argument used by'),
        _('LDAP search functions'))


@global_preferences_registry.register
class LdapServiceUser(StringPreference):
    """
    Dynamic preferences class controlling the service user to be used by
    :ref:`Active Directory Services Monitoring Application` background
    processes

    :access_key: 'ldapprobe__service_user'
    """
    section = LDAP_PROBE
    name = 'service_user'
    default = 'ldap_probe_service_user'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Service user for Domain Controllers Monitoring Application'
        ' background processes').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapExpireProbeLogEntries(DurationPreference):
    """
    Dynamic preferences class controlling how old `LDAP` probe log entries
    are before they are marked as `expired`

    :access_key: 'ldapprobe__ldap_expire_after'
    """
    section = LDAP_PROBE
    name = 'ldap_expire_after'
    default = settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'mark LDAP probe log entries as expired if older than').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapDeleteExpiredProbeLogEntries(BooleanPreference):
    """
    Dynamic preferences class controlling whether `expired` `LDAP` probe
    log entries will be deleted

    :access_key: 'ldapprobe__ldap_delete_expired'
    """
    section = LDAP_PROBE
    name = 'ldap_delete_expired'
    default = settings.CITRUS_BORG_DELETE_EXPIRED
    """default value for this dynamic preference"""
    required = False
    verbose_name = _('delete expired LDAP probe log entries').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapErrorAlertSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` error alerts

    :access_key: 'ldapprobe__ldap_error_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_error_subscription'
    default = 'LDAP: Error alerts subscription'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Email Subscription for LDAP Error Alerts').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapErrorReportSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` error reports

    :access_key: 'ldapprobe__ldap_error_report_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_error_report_subscription'
    default = 'LDAP: Error report'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Email Subscription for LDAP Error Reports').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapNonOrionADNodesReportSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` reports about `AD` nodes not defined
    on the `Orion` server

    :access_key: 'ldapprobe__ldap_non_orion_ad_nodes_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_non_orion_ad_nodes_subscription'
    default = 'LDAP: non Orion AD nodes'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Email Subscription for non Orion AD Nodes Reports').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapOrionADNodesFQDNReportSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` reports about `AD` nodes defined
    on the `Orion` server with missing FQDN values

    :access_key: 'ldapprobe__ldap_orion_fqdn_ad_nodes_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_orion_fqdn_ad_nodes_subscription'
    default = 'LDAP: Orion FQDN AD nodes'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Email Subscription for Orion AD Nodes FQDN Reports').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapOrionADNodesDupesReportSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` reports about duplicate `AD` nodes defined
    on the `Orion` server

    :access_key: 'ldapprobe__ldap_orion_dupes_ad_nodes_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_orion_dupes_ad_nodes_subscription'
    default = 'LDAP: Duplicate Orion AD nodes'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Email Subscription for duplicate Orion AD Nodes Reports').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfAlertSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` performance alerts

    :access_key: 'ldapprobe__ldap_perf_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_perf_subscription'
    default = 'LDAP: Performance alerts subscription'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Email Subscription for LDAP Performance Alerts').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfRaiseMinorAlerts(BooleanPreference):
    """
    Dynamic preferences class controlling whether minor alerts about AD
    services performance degradations will be raised

    By default, only response times larger than the value specified via
    :class:`LdapPerfNeverExceedThreshold` will trigger an alert. Response
    times larger than values defined by :class:`LdapPerfAlertThreshold` and
    :class:`LdapPerfWarnThreshold` will only be included in periodic
    reports with regards to performance degradation.

    :access_key: 'ldapprobe__ldap_perf_raise_all'
    """
    section = LDAP_PROBE
    name = 'ldap_perf_raise_all'
    default = False
    """default value for this dynamic preference"""
    required = False
    verbose_name = _(
        'Raise alerts for all LDAP performance degradation events.').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfDegradationReportGoodNews(BooleanPreference):
    """
    Dynamic preferences class controlling whether performance degradation
    reports with 'all is well, there is no performance degradation' will
    still be sent out via email

    :access_key: 'ldapprobe__ldap_perf_send_good_news'
    """
    section = LDAP_PROBE
    name = 'ldap_perf_send_good_news'
    default = False
    """default value for this dynamic preference"""
    required = False
    verbose_name = _(
        'LDAP: Send performance degradation reports even when there is no'
        ' performance degradation')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfNeverExceedThreshold(DecimalPreference):
    """
    Dynamic preferences class controlling the threshold
    used for dispatching red level alerts about `LDAP` performance degradation

    :access_key: 'ldapprobe__ldap_perf_err'
    """
    section = LDAP_PROBE
    name = 'ldap_perf_err'
    default = decimal.Decimal('1.000')
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'LDAP Performance Error Threshold for Immediate Alerts (in seconds)'
    ).title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfAlertThreshold(DecimalPreference):
    """
    Dynamic preferences class controlling the threshold
    used for generating error reports for `LDAP` performance degradation

    :access_key: 'ldapprobe__ldap_perf_alert'

    .. note::

        we are aware that the class name and the access keys for this class
        and :class:`LdapPerfNeverExceedThreshold` are not following the
        usual practice.
    """
    section = LDAP_PROBE
    name = 'ldap_perf_alert'
    default = decimal.Decimal('0.750')
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'LDAP Performance Error Threshold for Reports (in seconds)').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfWarnThreshold(DecimalPreference):
    """
    Dynamic preferences class controlling the threshold
    used for generating warning reports for `LDAP` performance degradation

    :access_key: 'ldapprobe__ldap_perf_warn'
    """
    section = LDAP_PROBE
    name = 'ldap_perf_warn'
    default = decimal.Decimal('0.500')
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'LDAP Performance Warning Threshold for Reports (in seconds)').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapReportPeriod(DurationPreference):
    """
    Dynamic preferences class controlling the period used for generating
    `LDAP` reports

    :access_key: 'ldapprobe__ldap_reports_period'
    """
    section = LDAP_PROBE
    name = 'ldap_reports_period'
    default = timezone.timedelta(hours=1)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Time interval to use when generating LDAP reports').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class SFTPAccount(StringPreference):
    """
    Dynamic preferences class for the user used to login for sftp tests

    :access_key: 'sftp__username'
    """
    section = SFTP_DEFAULTS
    name = 'username'
    default = 'LoginPI25@vch.ca'
    required = True
    verbose_name = _('The user that is used to login into SFTP server.')


@global_preferences_registry.register
class SFTPPassword(StringPreference):
    """
    Dynamic preferences class for the password used to login for sftp tests

    :access_key: 'sftp__password'
    """
    section = SFTP_DEFAULTS
    name = 'password'
    default = 'LoginPI1!'
    required = True
    verbose_name = _('The password that is used to login into SFTP server.')


def get_preference(key):
    """
    get the current value of a dynamic preference
    (also known as a dynamic setting)

    :arg str key: the accessor key for the preference
        it follows this format 'section__preference_name`
    """
    section, name = key.split('__')
    # TODO figure out how to get the cache working properly, instead of doing
    #      this weird workaround
    db_pref = global_preferences_registry.manager().get_db_pref(section, name)

    return db_pref.value


def get_list_preference(key):
    """
    get the a list from a dynamic preference
    (also known as a dynamic setting)

    :arg str key: the accessor key for the preference
        it follows this format 'section__preference_name`
    """
    return get_preference(key).split(',')


def get_int_list_preference(key):
    """
    get a list of ints from a dynamic preference


    :arg str key: the accessor key for the preference
        it follows this format 'section__preference_name`
    :return list: returns the list of integers represented by the string
                  preference
    """
    return [int(i) for i in get_list_preference(key)]
