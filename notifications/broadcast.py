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
        if pk is not None:
            self.connection = con
            self.obj = Notification.objects.get(pk=pk)
            email = self.get_defined_email_parameters()
        else:
            email = self.get_default_email_parameters()     

        self.send(email)

        if pk is not None:
            self.post_send_mail_update()

    def get_defined_email_parameters(self):
        '''
        creating  defined the email message
        '''
        receivers = self.obj.subcribers
        return {"subject":self.obj.message["rule_msg"],
                "message":self.obj.message,
                "from":settings.EMAIL_HOST_USER,
                "to":receivers,
                "con":self.connection
        }

    def get_default_email_parameters(self):
        '''
        creating  default email message
        '''
        return {"subject":EmailMessage.subject,
                "message":EmailMessage.message,
                "from":EmailMessage.from_email,
                "to":EmailMessage.to,
                "con":EmailMessage.connection
        }


    def post_send_mail_update(self):
        '''
        update notification columns upon successful email sent
        '''
        self.obj.objects.update(broadcast_on=timezone.now(), escalated_on=timezone.now() + timezone.timedelta(days=7))
        


    @classmethod
    def send(cls, email):
        '''
        override parent class send method
        '''
        super().__init__(email["message"],
                        email["from"],
                        email["to"],
                        None,
                        email["con"]
                        )
        super().send()

