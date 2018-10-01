"""
.. _utils:

utility  functions for the notification tasks

:module:    p_soc_auto.notification.utils

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

:update:    Oct. 01 2018

"""
from django.conf import settings
from django.core.mail import send_mail
from .models import Notification

def email(pk):
    """
    send email
    """
    ack_on = Notification.objects.filter(instance_pk=pk).values('ack_on')
    nType = Notification.objects.filter(instance_pk=pk).values('notification_type')
    nLevel = Notification.objects.filter(instance_pk=pk).values('notification_level')
    if ack_on is None:
        broadcast = NotificationTypeBroadcast.objects.filter(notification_type=nType).values('broadcast')
        nMessage = Notification.objects.filter(instance_pk=pk).message
        nSubscribers = Notification.objects.filter(instance_pk=pk).subscribers

        email_subject = "?"
        email_message = nMessage["rule"]
        email_from = settings.EMAIL_HOST_USER
        recipient_list = nSubscribers #['phsadev@gmail.com',]
        send_mail( subject, message, email_from, recipient_list )

