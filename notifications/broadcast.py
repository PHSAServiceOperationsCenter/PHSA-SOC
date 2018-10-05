"""
.. _utils:

utility  functions for the notification tasks

:module:    p_soc_auto.notification.utils

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

:update:    Oct. 04 2018

"""
import logging
from django.utils import timezone
from django.core.mail import get_connection
from django.core.mail.message import EmailMessage
from django.http import HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.core.mail import send_mail, BadHeaderError
from .models import Notification


class EmailBroadCast(EmailMessage):
    '''
        EmailBroadCast class to Broadcast Email
    '''

    def __init__(self, pk, \
                 fields = {'broadcast_on':timezone.now(), 'escalated_onNone':timezone.now()}, \
                 con = None):
        '''
        1.pk Notification pk
        2. Fields... fields need to be updated after email send
        we need to distinguish this parameter for both
        successfull on unsuccessfull email sent
        3. con this is smtp connection object assigned
        from setting.py if passed as None
        '''
        self.pk = pk
        self.fields = fields
        self.connection = con
        try:
            self.obj = Notification(pk=self.pk)
        except:
            self.obj = None

    def prepare_email_from_notification(self):
        """
        prepares notification email ...
        """
        if self.obj is not None:
            try:
                email = self.get_email_parameters()
                super().__init__(email["message"], email["from"], email["to"], None, email["con"])
            except Notification.DoesNotExist as ex:
                self.obj = None
                logging.info("Notification object does not exist %s", str(ex))
            except BadHeaderError as ex
                self.obj = None
                logging.info("Invalid header found. %s", str(ex))

    def get_email_parameters(self):
        '''
        creating  creating the email message
        '''
        receivers = self.obj.subcribers
        return {"subject":self.obj.message["rule_msg"], \
                "message":self.obj.message, \
                "from":settings.EMAIL_HOST_USER, \
                "to":receivers, \
                "con":self.connection
        }

    def post_send_mail_update(self):
        '''
        update notification columns upon successful email sent
        '''
        try:
            for attr, value in self.fields.items():
                setattr(self.obj, attr, value)
            self.obj.save()
        except Exception as ex:
            logging.info("Failed Updating Notification model... %s", \
                         str(ex))

    def send(self, *args, **kwargs):
        '''
        override parent class send method
        '''
        try:
            super().send(*args, **kwargs)
        except Exception as ex:
            logging.info("Failed Sending Email:.... %s", str(ex))
