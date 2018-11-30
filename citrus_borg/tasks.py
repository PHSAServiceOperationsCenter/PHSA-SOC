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
from celery import shared_task
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError
from django.conf import settings
from django.utils import timezone

from citrus_borg.locutus.communication import (
    get_dead_bots, get_dead_brokers, get_dead_sites,
)
from ssl_cert_tracker.models import Subscription
from ssl_cert_tracker.lib import Email

_logger = get_task_logger(__name__)


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
    from .locutus.assimilation import process_borg
    from .models import (
        WindowsLog, AllowedEventSource, WinlogbeatHost, KnownBrokeringDevice,
        WinlogEvent,
    )

    try:
        borg = process_borg(body)
    except Exception as error:
        msg = 'processing %s raises %s' % (body, str(error))
        _logger.error(msg)
        return msg

    try:
        event_host = WinlogbeatHost.get_or_create_from_borg(borg)
    except Exception as error:
        _logger.error(error)
        return 'failed %s' % str(error)

    try:
        event_broker = KnownBrokeringDevice.get_or_create_from_borg(borg)
    except Exception as error:
        _logger.error(error)
        return 'failed %s' % str(error)

    try:
        event_source = AllowedEventSource.objects.get(
            source_name=borg.event_source)
    except Exception as error:
        _logger.error(error)
        return 'failed %s' % str(error)

    try:
        windows_log = WindowsLog.objects.get(log_name=borg.windows_log)
    except Exception as error:
        _logger.error(error)
        return 'failed %s' % str(error)

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
        _logger.error(error)
        return 'failed %s' % str(error)

    return 'saved event: %s' % winlogevent


@shared_task(queue='citrus_borg')
def expire_events():
    """
    expire events
    """
    from .models import WinlogEvent

    expired = WinlogEvent.objects.filter(
        created_on__lt=timezone.now()
        - settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER).update(is_expired=True)

    if settings.CITRUS_BORG_DELETE_EXPIRED:
        WinlogEvent.objects.filter(is_expired=True).all().delete()
        return 'deleted %s events accumulated over the last %s' % (
            expired, settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER)

    return 'expired %s events accumulated over the last %s' % (
        expired, settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER)


@shared_task(queue='borg_chat', rate_limit='1/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_borgs_alerts(now=None, **dead_for):
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
    if now is None:
        now = timezone.now()

    if not isinstance(now, datetime.datetime):
        msg = (
            'invalid argument %s type %s, must be datetime.datetime'
        ) % (now, type(now))
        _logger.error(msg)
        return msg

    if not dead_for:
        dead_for = settings.CITRUS_BORG_DEAD_BOT_AFTER
    else:
        try:
            dead_for = timezone.timedelta(**dead_for)
        except Exception as error:
            msg = ('invalid argument %s, throws %s') % (dead_for, str(error))
            _logger.error(msg)
            return msg

    try:
        subscription = Subscription.objects.\
            get(subscription='Dead Citrix monitoring bots')
    except Exception as error:
        _logger.error('cannot retrieve subscription info: %s' % str(error))
        return 'cannot retrieve subscription info: %s' % str(error)

    try:
        email_alert = Email(
            data=get_dead_bots(now=now, time_delta=dead_for),
            subscription_obj=subscription, logger=_logger,
            time_delta=dead_for)
    except Exception as error:
        _logger.error('cannot initialize email object: %s' % str(error))
        return 'cannot initialize email object: %s' % str(error)

    try:
        return email_alert.send()
    except Exception as error:
        raise error


@shared_task(queue='borg_chat', rate_limit='1/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_dead_borgs_reports(now=None, **dead_for):
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
    if now is None:
        now = timezone.now()

    if not isinstance(now, datetime.datetime):
        msg = (
            'invalid argument %s type %s, must be datetime.datetime'
        ) % (now, type(now))
        _logger.error(msg)
        return msg

    if not dead_for:
        dead_for = settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER
    else:
        try:
            dead_for = timezone.timedelta(**dead_for)
        except Exception as error:
            msg = ('invalid argument %s, throws %s') % (dead_for, str(error))
            _logger.error(msg)
            return msg

    try:
        subscription = Subscription.objects.\
            get(subscription='Dead Citrix monitoring bots')
    except Exception as error:
        _logger.error('cannot retrieve subscription info: %s' % str(error))
        return 'cannot retrieve subscription info: %s' % str(error)

    try:
        email_alert = Email(
            data=get_dead_bots(now=now, time_delta=dead_for),
            subscription_obj=subscription, logger=_logger,
            time_delta=dead_for)
    except Exception as error:
        _logger.error('cannot initialize email object: %s' % str(error))
        return 'cannot initialize email object: %s' % str(error)

    try:
        return email_alert.send()
    except Exception as error:
        raise error
