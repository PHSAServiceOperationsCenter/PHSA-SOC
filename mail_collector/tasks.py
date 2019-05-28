"""
.. _tasks:

celery tasks for the mail_collector application

:module:    mail_collector.tasks

:copyright:

    Copyright 2018 - 2019Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    May 27, 2019

"""
import json
from celery import shared_task
from celery.utils.log import get_task_logger

from citrus_borg.locutus.assimilation import process_borg
from citrus_borg.models import WinlogbeatHost

LOGGER = get_task_logger(__name__)


@shared_task(queue='mail_collector')
def store_mail_data(body):
    """
    grab the exchange events from rabbitmq and dump it to the database
    """
    def reraise(msg, body, error):
        LOGGER.error('%s %s: %s', msg, body, str(error))
        raise error

    try:
        exchange_data = process_borg(body, LOGGER)
    except Exception as error:
        reraise('cannot extract exchange data from this event', body, error)

    try:
        event_host = (WinlogbeatHost.get_or_create_from_borg(exchange_data))
    except Exception as error:
        reraise('cannot retrieve bot info from event', body, error)
