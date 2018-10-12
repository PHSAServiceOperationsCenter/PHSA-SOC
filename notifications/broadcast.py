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
                 subject='default subject',
                 message='default_message', 
                 from_email='ali.rahmat@phsa.ca',
                 to=['ali.rahmat@phsa.ca',],
                 cc=[],
                 bcc=[],
                 connection=None,
                 attachments=[],
                 reply_to=['ali.rahmat@phsa.ca',], 
                 headers=None,
                 notification_pk=None,
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
        if notification_pk is not None:
            self.notification_pk = notification_pk
            self.obj = Notification.objects.get(pk=self.notification_pk)
            #email = self.get_defined_email_parameters()
            subject=self.obj.rule_msg
            body=self.obj.message
            # and all the other things from get_defined_email_parameters

        super().__init__(subject, message, from_email, to, bcc, connection,attachments,cc, reply_to, headers,*args, **kwargs)


    def get_defined_email_parameters(self):
        '''
        take this out
        creating  defined the email message
        '''
        receivers = self.obj.subcribers
        return {"subject":self.obj.message["rule_msg"],
                "message":self.obj.message,
                "from":self.email_from,
                "to":receivers,
                "con":self.connection
        }

    def get_default_email_parameters(self):
        '''
        take this out as well, default stuff comes fromt settings. there is an ADMINS or similar settings that
        should be the base
        creating  default email message
        '''
        return {"subject":self.subject,
                "message":self.message,
                "from":self.email_from,
                "to":self.email_to
                #"get_connection":self.connection
        }

    def post_send_mail_update(self):
        '''
        extend this to include the whole send and update logic
        
        update notification columns upon successful email sent
        '''
        Notification.objects.filter(pk=self.notification_pk).update(
            broadcast_on=timezone.now(),
            escalated_on=timezone.now() + timezone.timedelta(days=7))


