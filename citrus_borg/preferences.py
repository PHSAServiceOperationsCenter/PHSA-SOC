"""
citrus_borg.dynamic_preferences_registry
----------------------------------------

This module is used to provide run-time configurable settings.

See p_soc_auto_base.preferences for more info.

:copyright:

    Copyright 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from django.conf import settings
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import (
    BooleanPreference, StringPreference, DurationPreference, IntPreference,
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


# The way dynamic preferences are set-up in Django we need to have these data
# classes without public methods
# pylint: disable=too-few-public-methods


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


