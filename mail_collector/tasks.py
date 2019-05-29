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

from citrus_borg.locutus.assimilation import process_borg
from citrus_borg.models import WinlogbeatHost

from mail_collector import exceptions, models

LOGGER = get_task_logger(__name__)


@shared_task(queue='mail_collector', task_serializer='pickle')
def store_mail_data(body):
    """
    grab the exchange events from rabbitmq and dump it to the database
    """
    result = chain(extract_exchange_data_from_event.s(body),
                   update_borg_info.s(), create_exchange_event.s())()

    return result


@shared_task(queue='mail_collector', task_serializer='pickle')
def extract_exchange_data_from_event(body):
    """
    process the windows log events collected from the exchange monitoring
    client to a structure suitable for passing on to the relevant django
    model instance

    :arg dict body: the event data

        it arrives as a JSON structure from the
        winlogbeat + logstash + rabbitMQ collection mechanism and it is
        decoded by `<citrus_borg.consumers>`

    :raises: :exception:`<mail_collector.exceptions.BadEventDataError>`
    """
    try:
        return process_borg(body, LOGGER)
    except:  # @IgnorePep8
        raise exceptions.BadEventDataError(
            'cannot process event data from %s' % body)


@shared_task(queue='mail_collector', task_serializer='pickle')
def update_borg_info(exchange_borg):
    """
    create or update the host instance in
    :class:`<citrus_borg.models.WinlogbeatHost>`

    :raises: :exception:`<mail_collector.exceptions.BadHostDataFromEventError>`
    """
    try:
        exchange_borg.source_host = WinlogbeatHost.get_or_create_from_borg(
            exchange_borg)
    except:  # @IgnorePep8
        raise exceptions.BadHostDataFromEventError(
            'cannot update borg host info from %s' % str(exchange_borg))

    return exchange_borg


@shared_task(queue='mail_collector', task_serializer='pickle')
def create_exchange_event(exchange_borg):
    """
    create the event data instance in the mail_collector models
    """
    event_data = exchange_borg.borg_message[0]._asdict()

    event = models.MailBotLogEvent(**event_data)
    event.save()

    if exchange_borg.borg_message[1]:
        mail_data = exchange_borg.borg_message[1]._asdict()
        event = models.MailBotMessage(event=event, **mail_data)
        event.save()

    return event
