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
from smtplib import SMTPServerDisconnected, SMTPDataError, SMTPConnectError

from django.core.mail import get_connection

SMTP_CONNECTION = get_connection()


@shared_task(
    rate_limit='0.5/s', queue='email', retry_backoff=True,
    autoretry_for=(SMTPServerDisconnected, SMTPDataError, SMTPConnectError))
def send_email(pk, fields_to_update):
    """
    task executing all email broadcast
    """
    pass

@shared_task(
    rate_limit='0.5/s', queue='email', retry_backoff=True,
    autoretry_for=(SMTPServerDisconnected, SMTPDataError, SMTPConnectError))
def check_email_ack(pk):
    """
    task executing check_email_ack
    """
    pass