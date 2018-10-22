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

class EmailBroadCast:
    def __init__(self, pk, subscribers):
        self.pk = pk
        self.recipient_list = subscribers

    def go(self):
        """
        sends notification email ...
        """
        nObj = Notification(pk=pk)

        if nObj.ack_on is None:
            nType = nObj.notification_type
            nMessage = nObj.message
            email_subject = nMessage["rule_msg"]
            email_message = nMessage
            email_from = settings.EMAIL_HOST_USER
            try:
                send_mail( email_subject, email_message, email_from, self.recipient_list )#['phsadev@gmail.com',]
            except BadHeaderError as ex:
                print('send_email: Invalid header found. %s' % str(ex))
                return HttpResponse('Invalid header found.')
            return HttpResponseRedirect('/')
    


