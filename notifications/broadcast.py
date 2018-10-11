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

    def __init__(self, pk=None, con = None, **kwargs):

        '''
        1.pk Notification pk
        2. Fields... fields need to be updated after email send
        we need to distinguish this parameter for both
        successfull on unsuccessfull email sent
        3. con this is smtp connection object assigned
        from setting.py if passed as None
        '''
        self.fields = {}
        for key, value in kwargs.items():
            self.fields[key] = value

        self.connection = con
        if pk is not None:
            self.obj = Notification.objects.get(pk=pk)
            email = self.get_defined_email_parameters()
            super().__init__(email["message"],
                                email["from"],
                                email["to"],
                                None,
                                email["con"]
                                )
        else: #pk is None
            super().__init__(EmailMessage.message,
                            EmailMessage.subject=,
                            EmailMessage.from_email=,
                            EmailMessage.to=,
                            None,
                            EmailMessage.connection
                            )
            self.send()

    def get_defined_email_parameters(self):
        '''
        creating  creating the email message
        '''
        receivers = self.obj.subcribers
        return {"subject":self.obj.message["rule_msg"],
                "message":self.obj.message,
                "from":settings.EMAIL_HOST_USER,
                "to":receivers,
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
            logging.info("Failed Updating Notification model... %s",
                         str(ex))

    def send(self, *args, **kwargs):
        '''
        override parent class send method
        '''
        super().send(*args, **kwargs)
