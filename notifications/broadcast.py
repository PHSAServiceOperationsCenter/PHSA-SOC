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
                 subject='default subject_new',
                 message='default_message_new', 
                 email_from='ali.rahmat@phsa.ca',
                 email_to=['ali.rahmat@phsa.ca'],
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
        subject ="http:10.1.80.24:8000"
        if connection is not None:
            self.notification_pk = notification_pk
            self.obj = Notification.objects.get(pk=self.notification_pk)
            #email = self.get_defined_email_parameters()
            subject=self.obj.rule_msg
            body=self.obj.message
            subject = "http://10.1.80.24:8000/notifications"
            print (self.obj.rule_msg, subject)
            # and all the other things from get_defined_email_parameters

        super().__init__(subject,
                         message,
                         email_from,
                         email_to,
                         bcc,
                         connection,
                         attachments,
                         cc,
                         reply_to,
                         headers,
                         *args, **kwargs)
        self.send()
        if notification_pk:
            post_send_mail_update

    def post_send_mail_update(self):
        '''
        extend this to include the whole send and update logic
        
        update notification columns upon successful email sent
        days, seconds = duration.days, duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 60)
        return days, hours, minutes, seconds
        '''

        Notification.objects.filter(pk=self.notification_pk).update(
            broadcast_on=timezone.now())
        # we need to update escalated_on if no one paid
        #attension to email within
        # timezone.timedelta(instance.notification_type.escalate_within)


        # Notification.objects.filter(pk=self.notification_pk).update(
        #     escalated_on=timezone.now() +
        #     timezone.timedelta(instance.notification_type.escalate_within))


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
                 subject='default subject_new',
                 message='default_message_new', 
                 email_from='ali.rahmat@phsa.ca',
                 email_to=['ali.rahmat@phsa.ca'],
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
        subject ="http:10.1.80.24:8000"
        if connection is not None:
            self.notification_pk = notification_pk
            self.obj = Notification.objects.get(pk=self.notification_pk)
            #email = self.get_defined_email_parameters()
            subject=self.obj.rule_msg
            body=self.obj.message
            subject = "http://10.1.80.24:8000/notifications"
            print (self.obj.rule_msg, subject)
            # and all the other things from get_defined_email_parameters

        super().__init__(subject,
                         message,
                         email_from,
                         email_to,
                         bcc,
                         connection,
                         attachments,
                         cc,
                         reply_to,
                         headers,
                         *args, **kwargs)
        self.send()
        if notification_pk:
            post_send_mail_update

    def post_send_mail_update(self):
        '''
        extend this to include the whole send and update logic
        
        update notification columns upon successful email sent
        days, seconds = duration.days, duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 60)
        return days, hours, minutes, seconds
        '''

        Notification.objects.filter(pk=self.notification_pk).update(
            broadcast_on=timezone.now())
        # we need to update escalated_on if no one paid
        #attension to email within
        # timezone.timedelta(instance.notification_type.escalate_within)


        # Notification.objects.filter(pk=self.notification_pk).update(
        #     escalated_on=timezone.now() +
        #     timezone.timedelta(instance.notification_type.escalate_within))


