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
from smtplib import SMTPServerDisconnected, SMTPDataError, SMTPConnectError
from celery import shared_task
from django.core.mail import get_connection
from .broadcast import EmailBroadCast

SMTP_CONNECTION = get_connection()


# @shared_task(
#     rate_limit='0.5/s', queue='email', retry_backoff=True,
#     autoretry_for=(SMTPServerDisconnected, SMTPDataError, SMTPConnectError))
# Serban please restore above commented code once we figure out the issue
#issue for some reasons decorator with parameters cause celery worker
#not to pick up the task

@shared_task
def send_email(notification_pk, fields_to_update):
    """
    task executing all email broadcast
    """
    email = EmailBroadCast(notification_pk, fields_to_update)
    email.send()

@shared_task(
    rate_limit='0.5/s', queue='email', retry_backoff=True,
    autoretry_for=(SMTPServerDisconnected, SMTPDataError, SMTPConnectError))
def check_email_ack(notification_pk):
    """
    task executing check_email_ack
    """
    pass
