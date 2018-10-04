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
from django.http import HttpResponse, HttpResponseRedirect
from .models import Notification, NotificationType
from django.db.models import F


class NotificationAck:
    '''
        NotificationAck class to Check Notification response from receivers
    '''

    def __init__(self, pk):
        '''
        1.pk Notification pk
        '''
        self.pk = pk
        self.obj = Notification(pk=pk)



    def receiver_ack(self):
        """
        verify ack_on receiver_ack  ...
        """
        if self.obj.broadcast_on:
            ntObj = NotificationType.objects.filter(notification_type=F(self.obj.notification_type)).e
            exp_whitin = ntObj.
            )
            broadcast_methods = list(
                instance.notification_type.notification_broadcast.
                    all().values_list('broadcast', flat=True)
            )
            self.obj.notification_type.no.expire_within.all().values_list
            instance.notification_type.notification_broadcast.
            all().values_list('broadcast', flat=True)
        self.obj.save(broadcast_on=timezone.now(), \
                      escalated_on=timezone.now())
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
