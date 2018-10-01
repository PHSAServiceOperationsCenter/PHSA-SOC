"""
.. _tasks:

celery tasks for the notification app

:module:    p_soc_auto.notifications.tasks

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

:updated:    Sep. 25, 2018

"""
from django.utils import timezone
from celery import shared_task
from .utils import BroadCastUtil


@shared_task(rate_limit='0.5/s', queue='email')
def send_email_task(pk):
    """
    task executing all email broadcast
    """
    obj = BroadCastUtil()
    obj.email(pk)

@shared_task(rate_limit='0.5/s', queue='sms')
def send_sms_task(pk):
    """
    task executing all sms broadcast
    """
    pass






