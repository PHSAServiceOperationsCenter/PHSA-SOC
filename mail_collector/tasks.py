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

LOGGER = get_task_logger(__name__)


@shared_task(queue='mail_collector')
def store_mail_data(body):
    LOGGER.debug('HORSEY %s', body.get('event_data')['param1'])
    super_horsey = json.loads(body.get('event_data')['param1'])
    LOGGER.debug('HORSEY %s', super_horsey.keys())
