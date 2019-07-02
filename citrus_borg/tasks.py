"""
.. _tasks:

celery tasks for the citrus_borg application

:module:    citrus_borg.tasks

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated: Nov. 22, 2018

"""
import datetime
from smtplib import SMTPConnectError

from celery import shared_task, group
from celery.utils.log import get_task_logger
from citrus_borg.dynamic_preferences_registry import get_preference
from citrus_borg.locutus.assimilation import process_borg
from citrus_borg.locutus.communication import (
    get_dead_bots, get_dead_brokers, get_dead_sites,
    get_logins_by_event_state_borg_hour, raise_failed_logins_alarm,
    login_states_by_site_host_hour, raise_ux_alarm, get_failed_events,
)
from citrus_borg.models import (
    WindowsLog, AllowedEventSource, WinlogbeatHost, KnownBrokeringDevice,
    WinlogEvent, BorgSite,
)
from django.utils import timezone
from ssl_cert_tracker.lib import Email
from ssl_cert_tracker.models import Subscription


LOGGER = get_task_logger(__name__)


# pylint: disable=W0703,R0914


@shared_task(queue='citrus_borg')
def store_borg_data(body, rate_limit='5/s'):
    """
    insert data collected from the logstash + rabbitmq combination into the
    django database. we assume that the :arg:`<body>` is JSON encoded and is
    castable to a ``dict``

    hosts and citrix session servers identified in the event data are saved to
    the database if first seen; otherwise the corresponding rows are updated
    with a last seen time stamp

    generic :exception:`<Exception>` are raised and logged to the celery log
    if anything goes amiss while processing the event data
    """
    def reraise(msg, body, error):
        LOGGER.error('%s %s: %s', msg, body, str(error))
        raise error

    try:
        borg = process_borg(body)
    except Exception as error:
        reraise('cannot save event data from event', body, error)

    try:
        event_host = WinlogbeatHost.get_or_create_from_borg(borg)
    except Exception as error:
        reraise('cannot retrieve bot info from event', body, error)

    try:
        event_broker = KnownBrokeringDevice.get_or_create_from_borg(borg)
    except Exception as error:
        reraise('cannot retrieve session host info from event', body, error)

    try:
        event_source = AllowedEventSource.objects.get(
            source_name=borg.event_source)
    except Exception as error:
        reraise('cannot match event source for event', body, error)

    try:
        windows_log = WindowsLog.objects.get(log_name=borg.windows_log)
    except Exception as error:
        reraise('cannot match windows log info for event', body, error)

    user = WinlogEvent.get_or_create_user(
        get_preference('citrusborgcommon__service_user'))
    winlogevent = WinlogEvent(
        source_host=event_host, record_number=borg.record_number,
        event_source=event_source, windows_log=windows_log,
        event_state=borg.borg_message.state, xml_broker=event_broker,
        event_test_result=borg.borg_message.test_result,
        storefront_connection_duration=borg.borg_message.
        storefront_connection_duration,
        receiver_startup_duration=borg.borg_message.receiver_startup_duration,
        connection_achieved_duration=borg.borg_message.
        connection_achieved_duration,
        logon_achieved_duration=borg.borg_message.logon_achieved_duration,
        logoff_achieved_duration=borg.borg_message.logoff_achieved_duration,
        failure_reason=borg.borg_message.failure_reason,
        failure_details=borg.borg_message.failure_details,
        raw_message=borg.borg_message.raw_message,
        created_by=user, updated_by=user
    )

    try:
        winlogevent.save()
    except Exception as error:
        reraise('cannot save data collected from event', body, error)

    return 'saved event: %s' % winlogevent.uuid
# pylint: enable=R0914


@shared_task(queue='citrus_borg')
def expire_events():
    """
    expire events
    """
    expired = WinlogEvent.objects.filter(
        created_on__lt=timezone.now()
        - get_preference('citrusborgevents__expire_events_older_than')
    ).update(is_expired=True)

    if get_preference('citrusborgevents__delete_expired_events'):
        WinlogEvent.objects.filter(is_expired=True).all().delete()
        return 'deleted %s events accumulated over the last %s' % (
            expired, get_preference('citrusborgevents__expire_events_older_than'))

    return 'expired %s events accumulated over the last %s' % (
        expired, get_preference('citrusborgevents__expire_events_older_than'))


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_borgs_alert(now=None, send_no_news=None, **dead_for):
    """
    send out alerts about borgs that have not been seen within the date-time
    interval defined by :arg:`<now>` - :arg:`<**dead_for>`

    :arg now: the reference moment in time. by default this is the value
              returned by :method:`<django.utils.timezone.now>` but any
              valid ``datetime.datetime`` value is acceptable

    :arg **dead_for: dictionary style arguments suitable for
                     :method:`<django.utils.timezone.timedelta>`. examples:

                     * 10 minutes: minutes=10
                     * 10 hours: hours=10
                     * 10 hours and 10 minutes: hours=10, minutes=10

                     valid keys are days, hours, minutes, seconds and
                     valid values are ``float`` numbers
    """
    now = _get_now(now)

    if not dead_for:
        time_delta = get_preference('citrusborgnode__dead_bot_after')
    else:
        time_delta = _get_timedelta(**dead_for)

    if send_no_news is None:
        send_no_news = get_preference('citrusborgcommon__send_no_news')

    if not isinstance(send_no_news, bool):
        raise TypeError(
            'object {} type {} is not valid. must be boolean'.
            format(send_no_news, type(send_no_news))
        )

    data = get_dead_bots(now=now, time_delta=time_delta)
    if not data and send_no_news:
        return (
            'all monitoring bots were active between'
            ' {:%a %b %d, %Y %H:%M %Z} and {:%a %b %d, %Y %H:%M %Z}'.
            format(timezone.localtime(value=now),
                   timezone.localtime(now - time_delta))
        )

    try:
        return _borgs_are_hailing(
            data=data,
            subscription=_get_subscription('Dead Citrix monitoring bots'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_borgs_report(now=None, send_no_news=False, **dead_for):
    """
    send out reports about borgs that have not been seen within the date-time
    interval defined by :arg:`<now>` - :arg:`<**dead_for>`

    :arg now: the reference moment in time. by default this is the value
              returned by :method:`<django.utils.timezone.now>` but any
              valid ``datetime.datetime`` value is acceptable

    :arg **dead_for: dictionary style arguments suitable for
                     :method:`<django.utils.timezone.timedelta>`. examples:

                     * 10 minutes: minutes=10
                     * 10 hours: hours=10
                     * 10 hours and 10 minutes: hours=10, minutes=10

                     valid keys are days, hours, minutes, seconds and
                     valid values are ``float`` numbers
    """
    now = _get_now(now)

    if not dead_for:
        time_delta = get_preference('citrusborgnode__node_forgotten_after')
    else:
        time_delta = _get_timedelta(**dead_for)

    data = get_dead_bots(now=now, time_delta=time_delta)
    if not data and send_no_news:
        return (
            'all monitoring bots were active between'
            ' {:%a %b %d, %Y %H:%M %Z} and {:%a %b %d, %Y %H:%M %Z}'.
            format(timezone.localtime(value=now),
                   timezone.localtime(now - time_delta))
        )

    try:
        return _borgs_are_hailing(
            data=data,
            subscription=_get_subscription('Dead Citrix monitoring bots'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_sites_alert(now=None, send_no_news=None, **dead_for):
    """
    email alerts about dead sites

    all the email foo about citrus_borg entities look the same and could be
    condensed into a single function but it is easier to configure the
    task invocation from the django periodic tasks application if one
    doesn't have to provide a lot of complex arguments

    :arg datetime.datetime now: the reference moment in time, default now()

    :arg **dead_for: dictionary style arguments suitable for
                     :method:`<django.utils.timezone.timedelta>`. examples:

                     * 10 minutes: minutes=10
                     * 10 hours: hours=10
                     * 10 hours and 10 minutes: hours=10, minutes=10

                     valid keys are days, hours, minutes, seconds and
                     valid values are ``float`` numbers
    """
    now = _get_now(now)

    if not dead_for:
        time_delta = get_preference('citrusborgnode__dead_site_after')
    else:
        time_delta = _get_timedelta(**dead_for)

    if send_no_news is None:
        send_no_news = get_preference('citrusborgcommon__send_no_news')

    if not isinstance(send_no_news, bool):
        raise TypeError(
            'object {} type {} is not valid. must be boolean'.
            format(send_no_news, type(send_no_news))
        )

    data = get_dead_sites(now=now, time_delta=time_delta)
    if not data and send_no_news:
        return (
            'at least one monitoring bot on each site was active between'
            ' {:%a %b %d, %Y %H:%M %Z} and {:%a %b %d, %Y %H:%M %Z}'.
            format(timezone.localtime(value=now),
                   timezone.localtime(now - time_delta))
        )

    try:
        return _borgs_are_hailing(
            data=data,
            subscription=_get_subscription('Dead Citrix client sites'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_sites_report(now=None, send_no_news=False, **dead_for):
    """
    send reports about dead Ctirix client sites

    see other similar tasks for details
    """
    now = _get_now(now)

    if not dead_for:
        time_delta = get_preference('citrusborgnode__node_forgotten_after')
    else:
        time_delta = _get_timedelta(**dead_for)

    data = get_dead_sites(now=now, time_delta=time_delta)
    if not data and send_no_news:
        return (
            'at least one monitoring bot on each site was active between'
            ' {:%a %b %d, %Y %H:%M %Z} and {:%a %b %d, %Y %H:%M %Z}'.
            format(timezone.localtime(value=now),
                   timezone.localtime(now - time_delta))
        )

    try:
        return _borgs_are_hailing(
            data=data,
            subscription=_get_subscription('Dead Citrix client sites'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_servers_report(now=None, send_no_news=False, **dead_for):
    """
    send reports about dead Citrix app hosts

    see other similar tasks for details
    """
    now = _get_now(now)

    if not dead_for:
        time_delta = get_preference('citrusborgnode__node_forgotten_after')
    else:
        time_delta = _get_timedelta(**dead_for)

    data = get_dead_brokers(now=now, time_delta=time_delta)
    if not data and send_no_news:
        return (
            'all known Cerner session servers were active between'
            ' {:%a %b %d, %Y %H:%M %Z} and {:%a %b %d, %Y %H:%M %Z}'.
            format(timezone.localtime(value=now),
                   timezone.localtime(now - time_delta))
        )

    try:
        return _borgs_are_hailing(
            data=data,
            subscription=_get_subscription('Missing Citrix farm hosts'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_servers_alert(now=None, send_no_news=None, **dead_for):
    """
    send reports about dead Citrix app hosts

    see other similar tasks for details
    """
    now = _get_now(now)

    if not dead_for:
        time_delta = get_preference('citrusborgnode__node_forgotten_after')
    else:
        time_delta = _get_timedelta(**dead_for)

    if send_no_news is None:
        send_no_news = get_preference('citrusborgcommon__send_no_news')

    if not isinstance(send_no_news, bool):
        raise TypeError(
            'object {} type {} is not valid. must be boolean'.
            format(send_no_news, type(send_no_news))
        )

    data = get_dead_brokers(now=now, time_delta=time_delta)
    if not data and send_no_news:
        return (
            'all known Cerner session servers were active between'
            ' {:%a %b %d, %Y %H:%M %Z} and {:%a %b %d, %Y %H:%M %Z}'.
            format(timezone.localtime(value=now),
                   timezone.localtime(now - time_delta))
        )

    try:
        return _borgs_are_hailing(
            data=data,
            subscription=_get_subscription('Missing Citrix farm hosts'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_borg_login_summary_report(now=None, **dead_for):
    """
    send reports reports about logon events for each Citrix bot

    see other similar tasks for details
    """
    if not dead_for:
        time_delta = get_preference(
            'citrusborgevents__ignore_events_older_than')
    else:
        time_delta = _get_timedelta(**dead_for)

    try:
        return _borgs_are_hailing(
            data=get_logins_by_event_state_borg_hour(
                now=_get_now(now), time_delta=time_delta),
            subscription=_get_subscription('Citrix logon event summary'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat')
def email_sites_login_ux_summary_reports(now=None, site=None,
                                         borg_name=None, **reporting_period):
    """
    send reports reports about logon events for each Citrix bot

    see other similar tasks for details

    """
    if not reporting_period:
        time_delta = get_preference('citrusborgux__ux_reporting_period')
    else:
        time_delta = _get_timedelta(**reporting_period)

    sites = BorgSite.objects.filter(enabled=True)
    if site:
        sites = sites.filter(site__iexact=site)
    if not sites.exists():
        return 'site {} does not exist. there is no report to diseminate.'.\
            format(site)
    sites = sites.order_by('site').values_list('site', flat=True)

    site_host_arg_list = []
    for borg_site in sites:
        borg_names = WinlogbeatHost.objects.filter(
            site__site__iexact=borg_site, enabled=True)
        if borg_name:
            borg_names = borg_names.filter(host_name__iexact=borg_name)
        if not borg_names.exists():
            LOGGER.info(
                'there is no bot named %s on site %s. skipping report...',
                borg_name, borg_site)
            continue

        borg_names = borg_names.\
            order_by('host_name').values_list('host_name', flat=True)

        for host_name in borg_names:

            site_host_arg_list.append((borg_site, host_name))

    group(email_login_ux_summary.s(now, time_delta, site_host_args) for
          site_host_args in site_host_arg_list)()

    return 'bootstrapped logon state counts and ux evaluation for {}'.\
        format(site_host_arg_list)


@shared_task(
    queue='borg_chat', rate_limit='3/s', max_retries=3, serializer='pickle',
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_login_ux_summary(now, time_delta, site_host_args):
    """
    email a login event state count and ux evaluation for a given site and host
    """
    try:
        return _borgs_are_hailing(
            data=login_states_by_site_host_hour(
                now=now, time_delta=time_delta,
                site=site_host_args[0], host_name=site_host_args[1]),
            subscription=_get_subscription(
                'Citrix logon event and ux summary'),
            logger=LOGGER, time_delta=time_delta,
            site=site_host_args[0], host_name=site_host_args[1])
    except Exception as error:
        raise error


@shared_task(queue='borg_chat')
def email_ux_alarms(now=None, site=None, borg_name=None,
                    send_no_news=None,
                    ux_alert_threshold=None, **reporting_period):
    """
    bootstrap the process of sending email alerts about user experience
    faults

    """
    now = _get_now(now)

    if not reporting_period:
        time_delta = get_preference('citrusborgux__ux_alert_interval')
    else:
        time_delta = _get_timedelta(**reporting_period)

    if send_no_news is None:
        send_no_news = get_preference('citrusborgcommon__send_no_news')

    if not isinstance(send_no_news, bool):
        raise TypeError(
            'object {} type {} is not valid. must be boolean'.
            format(send_no_news, type(send_no_news))
        )

    if ux_alert_threshold is None:
        ux_alert_threshold = get_preference('citrusborgux__ux_alert_threshold')
    else:
        if not isinstance(ux_alert_threshold, dict):
            raise TypeError(
                'object {} type {} is not valid. must be a dictionary'
                ' suitable for datetime.timedelta() arguments'.format(
                    ux_alert_threshold, type(ux_alert_threshold)))

        ux_alert_threshold = _get_timedelta(**ux_alert_threshold)

    # TODO: refactor this; see https://trello.com/c/FeGO5Vqf
    sites = BorgSite.objects.filter(enabled=True)
    if site:
        sites = sites.filter(site__iexact=site)
    if not sites.exists():
        return 'site {} does not exist. there is no report to diseminate.'.\
            format(site)
    sites = sites.order_by('site').values_list('site', flat=True)

    site_host_arg_list = []
    for borg_site in sites:
        borg_names = WinlogbeatHost.objects.filter(
            site__site__iexact=borg_site, enabled=True)
        if borg_name:
            borg_names = borg_names.filter(host_name__iexact=borg_name)
        if not borg_names.exists():
            LOGGER.info(
                'there is no bot named %s on site %s. skipping report...',
                borg_name, borg_site)
            continue

        borg_names = borg_names.\
            order_by('host_name').values_list('host_name', flat=True)

        for host_name in borg_names:

            site_host_arg_list.append((borg_site, host_name))

    group(email_ux_alarm.s(now, time_delta, send_no_news,
                           ux_alert_threshold, site_host_args) for
          site_host_args in site_host_arg_list)()

    return 'bootstrapped ux evaluation alarms for {}'.\
        format(site_host_arg_list)


@shared_task(
    queue='borg_chat', rate_limit='3/s', max_retries=3, serializer='pickle',
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_ux_alarm(
        now, time_delta, send_no_news, ux_alert_threshold, site_host_args):
    """
    email an ux alarm for a given site and host
    """
    now = _get_now(now)
    site, host_name = site_host_args

    data = raise_ux_alarm(
        now=now, time_delta=time_delta,
        ux_alert_threshold=ux_alert_threshold,
        site=site, host_name=host_name)
    if not data and send_no_news:
        return (
            'Citrix response times on {} bot in {} were better than {} between'
            ' {:%a %b %d, %Y %H:%M %Z} and {:%a %b %d, %Y %H:%M %Z}'.
            format(host_name, site, ux_alert_threshold,
                   timezone.localtime(value=now),
                   timezone.localtime(now - time_delta))
        )

    try:
        return _borgs_are_hailing(
            data=data, subscription=_get_subscription('Citrix UX Alert'),
            logger=LOGGER, time_delta=time_delta,
            ux_alert_threshold=ux_alert_threshold,
            site=site_host_args[0], host_name=site_host_args[1])
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_failed_logins_alarm(now=None, failed_threshold=None, **dead_for):
    """
    email alerts about failed logins

    see other similar tasks for details
    """
    if failed_threshold is None:
        failed_threshold = get_preference(
            'citrusborglogon__logon_alert_threshold')

    if not dead_for:
        time_delta = get_preference('citrusborglogon__logon_alert_after')
    else:
        time_delta = _get_timedelta(**dead_for)

    now = _get_now(now)
    data = raise_failed_logins_alarm(
        now=now, time_delta=time_delta,
        failed_threshold=failed_threshold)

    if not data:
        return (
            'there were less than {} failed logon events between'
            ' {:%a %b %d, %Y %H:%M %Z} and {:%a %b %d, %Y %H:%M %Z}'.
            format(failed_threshold, timezone.localtime(value=now),
                   timezone.localtime(now - time_delta))
        )

    try:
        return _borgs_are_hailing(
            data=data, subscription=_get_subscription('Citrix logon alert'),
            logger=LOGGER, time_delta=time_delta,
            failed_threshold=failed_threshold)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_failed_logins_report(now=None, send_no_news=False, **dead_for):
    """
    send out the report with all known failed logon events
    """
    if not dead_for:
        time_delta = get_preference('citrusborglogon__logon_report_period')
    else:
        time_delta = _get_timedelta(**dead_for)

    now = _get_now(now)

    data = get_failed_events(now=now, time_delta=time_delta)

    if not data and send_no_news:
        return (
            'there were no failed logon events between'
            ' {:%a %b %d, %Y %H:%M %Z} and {:%a %b %d, %Y %H:%M %Z}'.
            format(timezone.localtime(value=now),
                   timezone.localtime(now - time_delta))
        )

    try:
        return _borgs_are_hailing(
            data=data,
            subscription=_get_subscription('Citrix Failed Logins Report'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat')
def email_failed_login_sites_report(
        now=None, site=None, borg_name=None,
        send_no_news=False, **reporting_period):
    """
    bootstrap emails for per site and bot failed login reports
    """
    if not reporting_period:
        time_delta = get_preference('citrusborglogon__logon_report_period')
    else:
        time_delta = _get_timedelta(**reporting_period)

        # TODO: refactor this; see https://trello.com/c/FeGO5Vqf
    sites = BorgSite.objects.filter(enabled=True)
    if site:
        sites = sites.filter(site__iexact=site)
    if not sites.exists():
        return 'site {} does not exist. there is no report to diseminate.'.\
            format(site)
    sites = sites.order_by('site').values_list('site', flat=True)

    site_host_arg_list = []
    for borg_site in sites:
        borg_names = WinlogbeatHost.objects.filter(
            site__site__iexact=borg_site, enabled=True)
        if borg_name:
            borg_names = borg_names.filter(host_name__iexact=borg_name)
        if not borg_names.exists():
            LOGGER.info(
                'there is no bot named %s on site %s. skipping report...',
                borg_name, borg_site)
            continue

        borg_names = borg_names.\
            order_by('host_name').values_list('host_name', flat=True)

        for host_name in borg_names:

            site_host_arg_list.append((borg_site, host_name))

    group(email_failed_login_site_report.s(now, time_delta,
                                           send_no_news, site_host_args) for
          site_host_args in site_host_arg_list)()

    return 'bootstrapped failed login reports for {}'.\
        format(site_host_arg_list)


@shared_task(
    queue='borg_chat', rate_limit='3/s', max_retries=3, serializer='pickle',
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_failed_login_site_report(
        now, time_delta, send_no_news, site_host_args):
    """
    email a report with the failed logon events for a specific site, bot pair
    """
    now = _get_now(now)
    site, host_name = site_host_args

    data = get_failed_events(
        now=now, time_delta=time_delta, site=site, host_name=host_name)
    if not data and send_no_news:
        return (
            'there were no failed logon events on the {} bot in {} between'
            ' {:%a %b %d, %Y %H:%M %Z} and {:%a %b %d, %Y %H:%M %Z}'.
            format(host_name, site, timezone.localtime(value=now),
                   timezone.localtime(now - time_delta))
        )

    try:
        return _borgs_are_hailing(
            data=data,
            subscription=_get_subscription(
                'Citrix Failed Logins per Site Report'),
            logger=LOGGER,
            time_delta=time_delta, site=site, host_name=host_name)
    except Exception as error:
        raise error


def _get_now(now=None):
    """
    :returns: a valid ``datetime.datetime`` object or ``datetime.dateime.now``
    """
    if now is None:
        now = timezone.now()

    if not isinstance(now, datetime.datetime):
        raise TypeError(
            'invalid argument %s type %s, must be datetime.datetime'
        ) % (now, type(now))

    return now


def _get_timedelta(**time_delta):
    """
    :returns: a valid ``datetime.timedelta`` objects
    """
    try:
        return timezone.timedelta(**time_delta)
    except Exception as error:
        raise error


def _borgs_are_hailing(data, subscription, logger, **extra_context):
    """
    prepare and send emails from the citrus_borg application
    """
    try:
        email_alert = Email(
            data=data, subscription_obj=subscription, logger=logger,
            **extra_context)
    except Exception as error:
        logger.error('cannot initialize email object: %s', str(error))
        return 'cannot initialize email object: %s' % str(error)

    try:
        return email_alert.send()
    except Exception as error:
        LOGGER.error(str(error))
        raise error


def _get_subscription(subscription):
    """
    :returns: a :class:`<ssl_cert_tracker.models.Subscription>` instance
    """
    try:
        return Subscription.objects.\
            get(subscription=subscription)
    except Exception as error:
        raise error

# pylint: enable=W0703
