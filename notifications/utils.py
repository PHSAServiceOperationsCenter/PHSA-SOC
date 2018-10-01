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
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
import smtplib
from .models import Notification

class BroadCastUtil:
    def __init__(self, broadCastMethod = "email"):
        self.broadCastMethod = broadCastMethod

    @staticmethod
    def email(pk):
        """
        Checks Notificatio ...
        """
        ack_on, nType, nLevel = \
            Notification.objects.filter \
            (instance_pk=pk).values\
            ('ack_on', 'notification_type', 'notification_level')
        if ack_on is None:
            broadcast = NotificationTypeBroadcast.objects.filter(notification_type=nType).values('broadcast')
            nMessage = Notification.objects.filter(instance_pk=pk).message
            nSubscribers = Notification.objects.filter(instance_pk=pk).subscribers

            email_subject = "?"
            email_message = nMessage
            email_from = settings.EMAIL_HOST_USER
            recipient_list = nSubscribers #['phsadev@gmail.com',]
            try:
                send_mail( subject, message, email_from, recipient_list )
            except BadHeaderError as ex:
                print('send_email: %s' % (ex.message))
                return HttpResponse('Invalid header found.')
            return HttpResponseRedirect('/')

