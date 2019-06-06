"""
.. _dynamic_preferences_registry:

dynamic preferences for the citrus_borg app

:module:    citrus_borg.dynamic_preferences_registry

:copyright:

    Copyright 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    jan. 3, 2019

"""
from django.conf import settings
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from dynamic_preferences.types import (
    BooleanPreference, StringPreference, DurationPreference, IntPreference,
    LongStringPreference, FloatPreference,
)
from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry

# pylint: disable=E1101,C0103
#=========================================================================
# E1101: instance of '__proxy__' has no 'title' member caused by using .title()
# on returns from gettext_lazy()
#
# C0103: asr PEP8 module level variables are constants and should be upper-case
#=========================================================================


citrus_borg_common = Section(
    'citrusborgcommon', verbose_name=_('citrus borg common settings').title())

citrus_borg_events = Section(
    'citrusborgevents', verbose_name=_('citrus borg event settings').title())

citrus_borg_node = Section(
    'citrusborgnode', verbose_name=_('Citrus Borg Node settings').title())

citrus_borg_ux = Section(
    'citrusborgux',
    verbose_name=_('Citrus Borg User Experience settings').title())

citrus_borg_logon = Section(
    'citrusborglogon',
    verbose_name=_('Citrus Borg Citrix Logon settings').title())

orion_server_conn = Section(
    'orionserverconn',
    verbose_name=_('Orion Server Connection Settings').title())

orion_filters = Section(
    'orionfilters',
    verbose_name=_('Filters used for Orion REST queries').title())

orion_probe_defaults = Section(
    'orionprobe',
    verbose_name=_('Filters used for Orion data probes').title())

email_prefs = Section('emailprefs', verbose_name=_(
    'Email preferences').title())

exchange = Section('exchange',
                   verbose_name=_('Options for the PHSA Service Operations Center'
                                  ' Exchange Monitoring Application'))


# pylint: enable=C0103

# pylint: disable=too-few-public-methods
@global_preferences_registry.register
class ExchangeEventSource(StringPreference):
    """
    configure the consumer for exchange monitoring events
    """
    section = exchange
    name = 'source'
    default = 'BorgExchangeMonitor'
    required = True
    verbose_name = _('Windows Logs Source for Exchange Monitoring Events ')
    help_text = _(
        'This is a list of values. Use "," to separate the list items')


@global_preferences_registry.register
class CitrusBorgEventSource(StringPreference):
    """
    configure consumer for Citrix events
    """
    section = citrus_borg_events
    name = 'source'
    default = 'ControlUp Logon Monitor'
    required = True
    verbose_name = _('Windows Logs Source for Citrix Events ').title()
    help_text = _(
        'This is a list of values. Use "," to separate the list items')


@global_preferences_registry.register
class EmailFromWhenDebug(StringPreference):
    """
    Use this when sending emails in the debug mode as the from_email
    """
    section = email_prefs
    name = 'from_email'
    default = 'serban.teodorescu@phsa.ca'
    required = True
    verbose_name = _('originating email address when in DEBUG mode').title()


@global_preferences_registry.register
class EmailToWhenDebug(StringPreference):
    """
    Use this when sending emails in the debug mode as the from_email
    """
    section = email_prefs
    name = 'to_emails'
    default = 'serban.teodorescu@phsa.ca,james.reilly@phsa.ca'
    required = True
    verbose_name = _('destination email addresses when in DEBUG mode').title()


@global_preferences_registry.register
class OrionProbeCSTOnly(BooleanPreference):
    """
    run data probes only against Cerner CST Orion Nodes
    """
    section = orion_probe_defaults
    name = 'cerner_cst'
    default = True
    required = False
    verbose_name = _('Only probe Cerner CST Orion nodes').title()


@global_preferences_registry.register
class OrionProbeKnownSslOnly(BooleanPreference):
    """
    run data probes only against Orion Nodes known to serve Ssl
    """
    section = orion_probe_defaults
    name = 'orion_ssl'
    default = False
    required = False
    verbose_name = _(
        'Only probe Orion nodes known to serve applications over SSL').title()


@global_preferences_registry.register
class OrionProbeServersOnly(BooleanPreference):
    """
    run data probes only against Orion Nodes categorized as server
    """
    section = orion_probe_defaults
    name = 'servers_only'
    default = True
    required = False
    verbose_name = _('Only probe Orion nodes categorized as servers').title()


@global_preferences_registry.register
class OrionCernerCSTFilter(StringPreference):
    """
    filter to extract Orion Nodes tagged as Cerner CST
    """
    section = orion_filters
    name = 'cerner_cst'
    default = 'Cerner-CST'
    required = True
    verbose_name = _('Query Filter for Cerner CST Orion nodes').title()


@global_preferences_registry.register
class OrionServerNodesFilter(StringPreference):
    """
    filter to run queries only against Orion Nodes of type 'server'
    """
    section = orion_filters
    name = 'server_node'
    default = 'server'
    required = True
    verbose_name = _('Query Filter for Orion server nodes').title()


@global_preferences_registry.register
class OrionAppSslFilter(StringPreference):
    """
    service or default user preference
    """
    section = orion_filters
    name = 'ssl_app'
    default = 'ssl'
    required = True
    verbose_name = _(
        'Query Filter for Orion nodes known to run applications over SSL'
    ).title()


@global_preferences_registry.register
class OrionServerUrl(LongStringPreference):
    """
    url used to create links to Orion Node server pages
    """
    section = orion_server_conn
    name = 'orion_server_url'
    default = settings.ORION_ENTITY_URL
    required = True
    verbose_name = _('Orion Server Root URL')


@global_preferences_registry.register
class OrionServerRestUrl(LongStringPreference):
    """
    url used to create links to Orion REST end points
    """
    section = orion_server_conn
    name = 'orion_rest_url'
    default = settings.ORION_URL
    required = True
    verbose_name = _('Orion Server REST API root URL')


@global_preferences_registry.register
class OrionServer(StringPreference):
    """
    orion user
    """
    section = orion_server_conn
    name = 'orion_hostname'
    default = settings.ORION_HOSTNAME
    required = True
    verbose_name = _('Orion Server Host Name or IP Address')


@global_preferences_registry.register
class OrionServerUser(StringPreference):
    """
    orion user
    """
    section = orion_server_conn
    name = 'orion_user'
    default = settings.ORION_USER
    required = True
    verbose_name = _('Orion Server User Name')


@global_preferences_registry.register
class OrionServerPassword(StringPreference):
    """
    orion password
    """
    section = orion_server_conn
    name = 'orion_password'
    default = settings.ORION_PASSWORD
    required = True
    verbose_name = _('Orion Server Password')


@global_preferences_registry.register
class OrionServerAcceptUnsignedCertificate(BooleanPreference):
    """
    orion user
    """
    section = orion_server_conn
    name = 'orion_verify_ssl_cert'
    default = settings.ORION_VERIFY_SSL_CERT
    required = False
    verbose_name = _('Ignore unsigned SSL certificate on the Orion server')


@global_preferences_registry.register
class OrionServerConnectionTimeout(FloatPreference):
    """
    orion server cconnection timeout
    """
    section = orion_server_conn
    name = 'orion_conn_timeout'
    default = settings.ORION_TIMEOUT[0]
    required = True
    verbose_name = _('Orion Server Connection Timeout')


@global_preferences_registry.register
class OrionServerReadTimeout(FloatPreference):
    """
    orion server read timeout
    """
    section = orion_server_conn
    name = 'orion_read_timeout'
    default = settings.ORION_TIMEOUT[1]
    required = True
    verbose_name = _('Orion Server Read Timeout')


@global_preferences_registry.register
class OrionServerRetry(IntPreference):
    """
    orion server retries
    """
    section = orion_server_conn
    name = 'orion_retry'
    default = settings.ORION_RETRY
    required = True
    verbose_name = _('Orion Server Connection Retries')


@global_preferences_registry.register
class OrionServerRetryBackoff(FloatPreference):
    """
    orion server retry backoff factor
    """
    section = orion_server_conn
    name = 'orion_backoff_factor'
    default = settings.ORION_BACKOFF_FACTOR
    required = True
    verbose_name = _('Orion Server Retry Backoff Factor')
    help_text = format_html(
        "See 'backoff_factor' at <a href={}>{}</a>",
        'https://urllib3.readthedocs.io/en/latest/reference/'
        'urllib3.util.html#module-urllib3.util.retry',
        _('Retry connection backoff factor'))


@global_preferences_registry.register
class ServiceUser(StringPreference):
    """
    service or default user preference
    """
    section = citrus_borg_common
    name = 'service_user'
    default = settings.CITRUS_BORG_SERVICE_USER
    required = True
    verbose_name = _('citrus borg service user').title()
    help_text = format_html(
        "{}<br>{}",
        _('default django user instance for background server processes.'),
        _('will be created automatically if it does not exist already'))


@global_preferences_registry.register
class SendNoNews(BooleanPreference):
    """
    send empty alerts preference
    """
    section = citrus_borg_common
    name = 'send_no_news'
    default = settings.CITRUS_BORG_NO_NEWS_IS_GOOD_NEWS
    required = False
    verbose_name = _("do not send empty citrix alert emails").title()
    help_text = format_html(
        "{}<br>{}",
        _('by default the application sends alert emails even if there is no'
          ' alert.'),
        _('enable this setting to only send alert emails if alerts have'
          ' occurred'))


@global_preferences_registry.register
class DeadAfter(DurationPreference):
    """
    reprot something as dead after preference
    """
    section = citrus_borg_common
    name = 'dead_after'
    default = settings.CITRUS_BORG_IGNORE_EVENTS_OLDER_THAN
    required = True
    verbose_name = _('dead if not seen for more than').title()
    help_text = format_html(
        "{}<br>{}",
        _('report a site, bot, or session host as dead if events mentioning'),
        _('them have not been received for more than this time period'))


@global_preferences_registry.register
class IgnoreEvents(DurationPreference):
    """
    ignore events older than preference
    """
    section = citrus_borg_events
    name = 'ignore_events_older_than'
    default = settings.CITRUS_BORG_IGNORE_EVENTS_OLDER_THAN
    required = True
    verbose_name = _('ignore events created older than').title()
    help_text = _(
        'events older than this value will not be used for any analysis')


@global_preferences_registry.register
class ExpireEvents(DurationPreference):
    """
    expire events older than preference
    """
    section = citrus_borg_events
    name = 'expire_events_older_than'
    default = settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER
    required = True
    verbose_name = _('mark events as expired if older than').title()
    help_text = _(
        'events older than this value will be marked as expired')


@global_preferences_registry.register
class DeleteExpireEvents(BooleanPreference):
    """
    delete expired eventss preference
    """
    section = citrus_borg_events
    name = 'delete_expired_events'
    default = settings.CITRUS_BORG_DELETE_EXPIRED
    required = False
    verbose_name = _('delete expired events').title()


@global_preferences_registry.register
class UxAlertThreshold(DurationPreference):
    """
    reprot something as dead after preference
    """
    section = citrus_borg_ux
    name = 'ux_alert_threshold'
    default = settings.CITRUS_BORG_UX_ALERT_THRESHOLD
    required = True
    verbose_name = _(
        'maximum acceptable response time for citrix events').title()
    help_text = format_html(
        "{}<br>{}",
        _('raise a user experience degraded alert if the response time for'),
        _('any monitored citrix event is higher than this value'))


@global_preferences_registry.register
class UxAlertInterval(DurationPreference):
    """
    reprot something as dead after preference
    """
    section = citrus_borg_ux
    name = 'ux_alert_interval'
    default = settings.CITRUS_BORG_UX_ALERT_INTERVAL
    required = True
    verbose_name = _('alert monitoring interval for citrix events').title()
    help_text = format_html(
        "{}<br>{}",
        _('measure the user experience response time for citrix events'),
        _('once per this time interval for every site/bot combination'))


@global_preferences_registry.register
class UxReportingPeriod(DurationPreference):
    """
    reprot something as dead after preference
    """
    section = citrus_borg_ux
    name = 'ux_reporting_period'
    default = settings.CITRUS_BORG_SITE_UX_REPORTING_PERIOD
    required = True
    verbose_name = _('user experience reporting period').title()
    help_text = format_html(
        "{}<br>{}",
        _('email a report with the citrix event response time averaged'),
        _('per hour for each site, bot comination over this time interval'))


@global_preferences_registry.register
class NodeForgottenAfter(DurationPreference):
    """
    reprot something as dead after preference
    """
    section = citrus_borg_node
    name = 'node_forgotten_after'
    default = settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER
    required = True
    verbose_name = _('reporting period for dead nodes').title()
    help_text = format_html(
        "{}<br>{}",
        _('reports about dead bots, site, or session hosts are based'),
        _('on this period'))


@global_preferences_registry.register
class BotAlertAfter(DurationPreference):
    """
    reprot something as dead after preference
    """
    section = citrus_borg_node
    name = 'dead_bot_after'
    default = settings.CITRUS_BORG_DEAD_BOT_AFTER
    required = True
    verbose_name = _('bot not seen alert threshold').title()
    help_text = format_html(
        "{}<br>{}",
        _('raise an alert if a bot has not sent any events for a period'),
        _('longer than this time interval'))


@global_preferences_registry.register
class SiteAlertAfter(DurationPreference):
    """
    reprot something as dead after preference
    """
    section = citrus_borg_node
    name = 'dead_site_after'
    default = settings.CITRUS_BORG_DEAD_SITE_AFTER
    required = True
    verbose_name = _('site not seen alert threshold').title()
    help_text = format_html(
        "{}<br>{}",
        _('raise an alert if none of the bots on a site has sent any events'),
        _('for a period longer than this time interval'))


@global_preferences_registry.register
class SessionHostAlertAfter(DurationPreference):
    """
    reprot something as dead after preference
    """
    section = citrus_borg_node
    name = 'dead_session_host_after'
    default = settings.CITRUS_BORG_DEAD_BROKER_AFTER
    required = True
    verbose_name = _('session host not seen alert threshold').title()
    help_text = format_html(
        "{}<br>{}<br>{}<br>{}",
        _('raise an alert if a known session host has not served any Citrix'),
        _('requests for a period longer than this time interval.'),
        _('note that session hosts are owned by Cerner and these alerts are'),
        _('mostly informative in nature'))


@global_preferences_registry.register
class FailedLogonAlertInterval(DurationPreference):
    """
    reprot something as dead after preference
    """
    section = citrus_borg_logon
    name = 'logon_alert_after'
    default = settings.CITRUS_BORG_FAILED_LOGON_ALERT_INTERVAL
    required = True
    verbose_name = _('failed logons alert interval').title()
    help_text = format_html(
        "{}<br>{}",
        _('interval at which to verify sites and bots for failed logon'),
        _('events'))


@global_preferences_registry.register
class FailedLogonAlertThreshold(IntPreference):
    """
    failed logon events count threshold preference
    """
    section = citrus_borg_logon
    name = 'logon_alert_threshold'
    required = True
    default = settings.CITRUS_BORG_FAILED_LOGON_ALERT_THRESHOLD
    verbose_name = _('failed logon events count alert threshold').title()
    help_text = format_html(
        "{}<br>{}",
        _('how many times does a failed logon happen in a given interval'),
        _('before an alert is raised'))


@global_preferences_registry.register
class LogonReportsInterval(DurationPreference):
    """
    report interval for logon events preference
    """
    section = citrus_borg_logon
    name = 'logon_report_period'
    default = settings.CITRUS_BORG_FAILED_LOGONS_PERIOD
    required = True
    verbose_name = _('logon events reporting period').title()
    help_text = format_html(
        "{}<br>{}",
        _('logon reports are calculated, created, and sent over this'),
        _('time interval'))
# pylint: disable=too-few-public-methods
# pylint: enable=E1101


def get_preference(key=None):
    """
    get the preference
    """
    preferences = global_preferences_registry.manager().load_from_db()
    try:
        return preferences.get(key)
    except Exception as error:
        raise error
