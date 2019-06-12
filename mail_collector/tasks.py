"""
.. _tasks:

celery tasks for the mail_collector application

:module:    mail_collector.tasks

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    May 27, 2019

"""
from celery import shared_task, chain
from celery.utils.log import get_task_logger

from django.utils import timezone


from citrus_borg.locutus.assimilation import process_borg
from citrus_borg.models import WinlogbeatHost
from citrus_borg.dynamic_preferences_registry import get_preference

from mail_collector import exceptions, models, lib
from p_soc_auto_base.utils import get_base_queryset

LOGGER = get_task_logger(__name__)


@shared_task(queue='mail_collector')
def store_mail_data(body):
    """
    grab the exchange events from rabbitmq and dump it to the database
    """
    try:
        exchange_borg = process_borg(body, LOGGER)
    except Exception as error:
        raise exceptions.BadEventDataError(
            'cannot process event data from %s, error: %s'
            % (body, str(error)))

    try:
        source_host = WinlogbeatHost.get_or_create_from_borg(
            exchange_borg)
    except Exception as error:
        raise exceptions.BadHostDataFromEventError(
            'cannot update borg host info from %s, error: %s'
            % str(exchange_borg, str(error)))

    event_data = exchange_borg.mail_borg_message[0]

    try:
        event = models.MailBotLogEvent(
            source_host=source_host,
            event_group_id=event_data.event_group_id,
            event_status=event_data.event_status,
            event_type=event_data.event_type,
            event_type_sort=lib.event_sort_code(event_data.event_type),
            mail_account=event_data.mail_account,
            event_message=event_data.event_message,
            event_body=event_data.event_body,
            event_exception=event_data.event_exception)
        event.save()
    except Exception as error:
        raise exceptions.SaveExchangeEventError(
            'cannot save event %s, error: %s' % (str(event_data), str(error)))

    if exchange_borg.mail_borg_message[1]:
        mail_data = exchange_borg.mail_borg_message[1]
        try:
            event = models.MailBotMessage(
                event=event,
                mail_message_identifier=mail_data.mail_message_identifier,
                sent_from=mail_data.sent_from, sent_to=mail_data.sent_to,
                received_from=mail_data.received_from,
                received_by=mail_data.received_by,
                mail_message_created=mail_data.mail_message_created,
                mail_message_sent=mail_data.mail_message_sent,
                mail_message_received=mail_data.mail_message_received)
            event.save()
        except Exception as error:
            raise exceptions.SaveExchangeMailEventError(
                'cannot save event %s, error: %s' % (str(event_data),
                                                     str(error)))

        return ('created exchange monitoring event from email message %s'
                % event.mail_message_identifier)

    return 'created exchange monitoring event %s' % event.uuid


@shared_task(queue='mail_collector')
def expire_events():
    """
    expire and/or delete events
    """
    moment = timezone.now() - get_preference('exchange__expire_events')
    queryset = get_base_queryset(
        'mail_collector.mailbotlogevent', event_registered_on__lte=moment)

    queryset.update(is_expired=True)

    if get_preference('exchange__delete_expired'):
        queryset.all().delete()

    return ('exchange events older than %s have expired'
            % get_preference('exchange__expire_events'))


@shared_task(queue='mail_collector')
def raise_exchange_server_alarms():
    """
    raise alarms for exchange servers
    """
    pass
