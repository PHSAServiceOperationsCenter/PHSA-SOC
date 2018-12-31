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

from django.conf import settings
from django.utils import timezone

from celery import shared_task, group
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger

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
from ssl_cert_tracker.lib import Email
from ssl_cert_tracker.models import Subscription


LOGGER = get_task_logger(__name__)

# pylint: disable=W0703,R0914


@shared_task(queue='citrus_borg')
def store_borg_data(body):
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
    try:
        borg = process_borg(body)
    except Exception as error:
        msg = 'processing %s raises %s' % (body, str(error))
        LOGGER.error(msg)

    try:
        event_host = WinlogbeatHost.get_or_create_from_borg(borg)
    except Exception as error:
        LOGGER.error(error)

    try:
        event_broker = KnownBrokeringDevice.get_or_create_from_borg(borg)
    except Exception as error:
        LOGGER.error(error)

    try:
        event_source = AllowedEventSource.objects.get(
            source_name=borg.event_source)
    except Exception as error:
        LOGGER.error(error)

    try:
        windows_log = WindowsLog.objects.get(log_name=borg.windows_log)
    except Exception as error:
        LOGGER.error(error)

    user = WinlogEvent.get_or_create_user(settings.CITRUS_BORG_SERVICE_USER)
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
        created_by=user, updated_by=user
    )

    try:
        winlogevent.save()
    except Exception as error:
        LOGGER.error(error)

    return 'saved event: %s' % winlogevent.uuid
# pylint: enable=R0914


@shared_task(queue='citrus_borg')
def expire_events():
    """
    expire events
    """
    expired = WinlogEvent.objects.filter(
        created_on__lt=timezone.now()
        - settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER).update(is_expired=True)

    if settings.CITRUS_BORG_DELETE_EXPIRED:
        WinlogEvent.objects.filter(is_expired=True).all().delete()
        return 'deleted %s events accumulated over the last %s' % (
            expired, settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER)

    return 'expired %s events accumulated over the last %s' % (
        expired, settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER)


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_borgs_alert(now=None, **dead_for):
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
    if not dead_for:
        time_delta = settings.CITRUS_BORG_DEAD_BOT_AFTER
    else:
        time_delta = _get_timedelta(**dead_for)

    try:
        return _borgs_are_hailing(
            data=get_dead_bots(now=_get_now(now), time_delta=time_delta),
            subscription=_get_subscription('Dead Citrix monitoring bots'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_borgs_report(now=None, **dead_for):
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
    if not dead_for:
        time_delta = settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER
    else:
        time_delta = _get_timedelta(**dead_for)

    try:
        return _borgs_are_hailing(
            data=get_dead_bots(now=_get_now(now), time_delta=time_delta),
            subscription=_get_subscription('Dead Citrix monitoring bots'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_sites_alert(now=None, **dead_for):
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
    if not dead_for:
        time_delta = settings.CITRUS_BORG_DEAD_SITE_AFTER
    else:
        time_delta = _get_timedelta(**dead_for)

    try:
        return _borgs_are_hailing(
            data=get_dead_sites(now=_get_now(now), time_delta=time_delta),
            subscription=_get_subscription('Dead Citrix client sites'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_sites_report(now=None, **dead_for):
    """
    send reports about dead Ctirix client sites

    see other similar tasks for details
    """
    if not dead_for:
        time_delta = settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER
    else:
        time_delta = _get_timedelta(**dead_for)

    try:
        return _borgs_are_hailing(
            data=get_dead_sites(now=_get_now(now), time_delta=time_delta),
            subscription=_get_subscription('Dead Citrix client sites'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_servers_report(now=None, **dead_for):
    """
    send reports about dead Citrix app hosts

    see other similar tasks for details
    """
    if not dead_for:
        time_delta = settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER
    else:
        time_delta = _get_timedelta(**dead_for)

    try:
        return _borgs_are_hailing(
            data=get_dead_brokers(now=_get_now(now), time_delta=time_delta),
            subscription=_get_subscription('Missing Citrix farm hosts'),
            logger=LOGGER, time_delta=time_delta)
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_servers_alert(now=None, **dead_for):
    """
    send reports about dead Citrix app hosts

    see other similar tasks for details
    """
    if not dead_for:
        time_delta = settings.CITRUS_BORG_DEAD_BROKER_AFTER
    else:
        time_delta = _get_timedelta(**dead_for)

    try:
        return _borgs_are_hailing(
            data=get_dead_brokers(now=_get_now(now), time_delta=time_delta),
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
        time_delta = settings.CITRUS_BORG_IGNORE_EVENTS_OLDER_THAN
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
        time_delta = settings.CITRUS_BORG_SITE_UX_REPORTING_PERIOD
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
                'there is no bot named {} on site {}. skipping report...'.
                format(borg_name, borg_site))
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
                    ux_alert_threshold=None, **reporting_period):
    """
    bootstrap the process of sending email alerts about user experience
    faults

    """
    if not reporting_period:
        time_delta = settings.CITRUS_BORG_UX_ALERT_INTERVAL
    else:
        time_delta = _get_timedelta(**reporting_period)

    if ux_alert_threshold is None:
        ux_alert_threshold = settings.CITRUS_BORG_UX_ALERT_THRESHOLD
    else:
        if not isinstance(ux_alert_threshold, dict):
            raise TypeError(
                'object {} type {} is not valid. must be a dictionary'
                ' suitable for datetime.timedelta() arguments'.format(
                    ux_alert_threshold, type(ux_alert_threshold)))

        ux_alert_threshold = _get_timedelta(**ux_alert_threshold)

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
                'there is no bot named {} on site {}. skipping report...'.
                format(borg_name, borg_site))
            continue

        borg_names = borg_names.\
            order_by('host_name').values_list('host_name', flat=True)

        for host_name in borg_names:

            site_host_arg_list.append((borg_site, host_name))

    group(email_ux_alarm.s(now, time_delta,
                           ux_alert_threshold, site_host_args) for
          site_host_args in site_host_arg_list)()

    return 'bootstrapped ux evaluation alarms for {}'.\
        format(site_host_arg_list)


@shared_task(
    queue='borg_chat', rate_limit='3/s', max_retries=3, serializer='pickle',
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_ux_alarm(now, time_delta, ux_alert_threshold, site_host_args):
    """
    email an ux alarm for a given site and host
    """
    try:
        return _borgs_are_hailing(
            data=raise_ux_alarm(
                now=now, time_delta=time_delta,
                ux_alert_threshold=ux_alert_threshold,
                site=site_host_args[0], host_name=site_host_args[1]),
            subscription=_get_subscription('Citrix UX Alert'),
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
        failed_threshold = settings.CITRUS_BORG_FAILED_LOGON_ALERT_THRESHOLD

    if not dead_for:
        time_delta = settings.CITRUS_BORG_FAILED_LOGON_ALERT_INTERVAL
    else:
        time_delta = _get_timedelta(**dead_for)

    now = _get_now(now)
    data = raise_failed_logins_alarm(
        now=now, time_delta=time_delta,
        failed_threshold=failed_threshold)

    if not data:
        return (
            'there were less than {} failed logon events between'
            ' {:%a %b %-m, %Y %H:%M %Z} and {:%a %b %-m, %Y %H:%M %Z}'.
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
def email_failed_logins_report(
        now=None, send_no_news=settings.CITRUS_BORG_NO_NEWS_IS_GOOD_NEWS,
        **dead_for):
    """
    send out the report with all known failed logon events
    """
    if not dead_for:
        time_delta = settings.CITRUS_BORG_FAILED_LOGONS_PERIOD
    else:
        time_delta = _get_timedelta(**dead_for)

    now = _get_now(now)

    data = get_failed_events(now=now, time_delta=time_delta)

    if not data and send_no_news:
        return (
            'there were no failed logon events between'
            ' {:%a %b %-m, %Y %H:%M %Z} and {:%a %b %-m, %Y %H:%M %Z}'.
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
        logger.error('cannot initialize email object: %s' % str(error))
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
