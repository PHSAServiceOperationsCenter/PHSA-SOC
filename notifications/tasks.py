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
# from django.utils import timezone
# from celery import shared_task, group


# from .models import RegexRule, IntervalRule, ExpirationRule

# from .broadcast_utils import EmailNotification

# @shared_task(rate_limit='0.5/s', queue='dispatch_message')
# def dispatch_message(notification_id):
#     """
#     celery task wrapper for the dispatching broadcast methods
#     """
#     setNotificationObject(notification_id)

# @shared_task(rate_limit='0.5/s', queue='email')
# def send_email(pk):
#     """
#     task executing all email broadcast
#     """
      print ("send_email")
      pass


# @shared_task(rate_limit='0.5/s', queue='sms')
# def send_sms(pk):
#     """
#     task executing all email broadcast
#     """
      print ("send_sms")
      pass





