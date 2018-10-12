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

    def __init__(self,
                 notification_pk=None,
                 connection=None,
                 subject='default subject',
                 message='default_message', 
                 email_from='ali.rahmat@phsa.ca',
                 email_to='ali.rahmat@phsa.ca', 
                 *args,
                 **kwargs
                ):

        '''
        1.pk Notification pk
        2. con this is smtp connection object assigned
        from setting.py if passed as None
        3. subject
        4.message
        5.email_from
        6.email_to
        7. fields  we need to distinguish this parameter for both
        successfull on unsuccessfull email sent
        
        '''
        if connection is not None:
            self.connection = connection
        if notification_pk is not None:
            self.obj = Notification.objects.get(pk=pk)
            email = self.get_defined_email_parameters()
        else:
            self.subject = subject
            self.message = message
            self.email_from = email_from
            self.email_to = email_to
            email = self.get_default_email_parameters()  

        super().__init__(*args, **kwargs)   

        self.send(email)

        if notification_pk is not None:
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
        return {"subject":self.subject,
                "message":self.message,
                "from":self.email_from,
                "to":self.email_to
        }

    def post_send_mail_update(self):
        '''
        update notification columns upon successful email sent
        '''
        self.obj.objects.update(broadcast_on=timezone.now(), escalated_on=timezone.now() + timezone.timedelta(days=7))
        

    def send(self, *args, **kwargs):
        '''
        override parent class send method
        '''
        super().send(*args, **kwargs)

