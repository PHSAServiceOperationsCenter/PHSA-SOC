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
from celery import shared_task
from celery.utils.log import get_task_logger
from django.conf import settings
from django.utils import timezone

_logger = get_task_logger(__name__)


@shared_task(queue='citrus_borg')
def store_borg_data(body):
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
        -settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER).update(is_expired=True)

    if settings.CITRUS_BORG_DELETE_EXPIRED:
        WinlogEvent.objects.filter(is_expired=True).all().delete()
        return 'deleted %s events accumulated over the last %s' % (
            expired, settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER)

    return 'expired %s events accumulated over the last %s' % (
        expired, settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER)
