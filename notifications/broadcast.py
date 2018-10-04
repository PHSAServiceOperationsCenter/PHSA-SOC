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
import smtplib
from .models import Notification


class EmailBroadCast(EmailMessage):
    '''
        EmailBroadCast class to Broadcast Email
    '''

    def __init__(self, pk, fields, con = None):
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
        self.obj = Notification(pk=pk)
        if con is None:
            self.connection = self.get_connection()
        else:
            self.connection = con

    def prepare_email_from_notification(self):
        """
        prepares notification email ...
        """
        email_parameters = self.prepare_email_message()
        try:
            email = EmailMessage(email_parameters["subject"], \
                                 email_parameters["message"], \
                                 to=email_parameters["receivers"], \
                                 from_email=email_parameters["sender"], \
                                 connection=self.connection)

            if self.send(EmailMessage):
                self.post_send_mail_update()
        except BadHeaderError as ex:
            print('send_email: Invalid header found. %s'\
                  % str(ex))
            return HttpResponse('Invalid header found.')
        return HttpResponseRedirect('/')

    def get_connection(self):
        """
            build connection from settings.py
        """
        return get_connection(use_tls=True, \
                              host=settings.EMAIL_HOST, \
                              port=settings.EMAIL_PORT, \
                              username=settings.EMAIL_HOST_PASSWORD, \
                              password=settings.EMAIL_HOST_USER)

    def prepare_email_message(self):
        '''
        creating  creating the email message
        '''
        receivers = list(self.obj.notification_type.all(). \
                         values_list('subscribers', flat=True))

        return {"receivers": receivers,
                "sender": settings.EMAIL_HOST_USER,
                "message": self.obj.message,
                "subject": self.obj.message["rule_msg"],
               }

    def post_send_mail_update(self):
        '''
        update notification columns upon successful email sent
        :return:
        '''
        try:
            self.obj.save(broadcast_on=timezone.now(), \
                          escalated_on =timezone.now())
        except Exception as ex:
            logging.info("Failed Updating Notification model... %s", \
                         str(ex))

    def send(self, *args, **kwargs):
        '''
        override parent class send method
        '''
        try:
            super().send(*args, **kwargs)
            return True
        except Exception as ex:
            logging.info("Failed Sending Email:.... %s", str(ex))
            return False
