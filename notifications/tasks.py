"""
.. _tasks:

celery tasks for the notification app

:module:    p_soc_auto.notifications.tasks

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca, serban.teodorescu@phsa.ca

:updated:    Sep. 25, 2018

"""
from celery import shared_task


@shared_task(rate_limit='0.5/s', queue='email')
def send_email(pk, fields_to_update):
    """
    task executing all email broadcast
    """
    pass
