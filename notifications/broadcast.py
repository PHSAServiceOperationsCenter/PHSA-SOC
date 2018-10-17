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
from django.utils import timezone
from django.core.mail.message import EmailMessage
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from django.conf import settings
from .models import Notification

class EmailBroadCast(EmailMessage):
    """
    EmailBroadCast class to Broadcast Email
    This class instanciated either by a third party or
    from signals.py through celery tasks worker
    """

    def __init__(self,
                 subject=settings.DEFAULT_EMAIL_SUBJECT,
                 message=settings.DEFAULT_EMAIL_MESSAGE,
                 email_from=settings.ADMINS[0][1],
                 email_to=None,
                 cc=settings.DEFAULT_EMAIL_CC,
                 bcc=settings.DEFAULT_EMAIL_BCC,
                 connection=settings.DEFAULT_EMAIL_CONNECTION,
                 attachments=None,
                 reply_to=settings.DEFAULT_EMAIL_REPLY_TO,
                 headers=settings.DEFAULT_EMAIL_HEADERS,
                 notification_pk=settings.DEFAULT_NOTIFICATION_PK,
                 email_type=settings.DEFAULT_EMAIL_TYPE,
                 *args,
                 **kwargs
                ):

        """
        Parameters:
        subject  (str) if None raise Exception
        message  (str)  if None raise Exception
        email_from (str) if None or invalid format raise Exception
        email_to  (list) if None or empty list or
                         invalid format raise Exception
        cc (list) if None ok
                  if list not empty and invalid format
                  raise Exception
        bcc if None ok
                  if list not empty and invalid format
                  raise Exception
        connection if None ok
        attachments if list not empty and invalid format
                     raise Exception
        reply_to (list) if None or empty list or
                         invalid format raise Exception
        headers None ok
        notification_pk None ok else must be a valid pk
        email_type= 0:subscribers
                    1:esc.
                    2: sub & esc.
                    otherwise:subscribers
        *args    TBD,
        **kwargs TBD
        """
        self.obj = None

        if notification_pk is None:
            if subject is None or message is None:
                raise Exception("Email Subject/Message")

            try:
                validate_email(email_from)
            except ValidationError:
                raise Exception("Invalid Email From")

            self.validate_email_types(email_to)
            self.validate_list_types([cc, bcc])
            self.validate_email_types(reply_to)
            if attachments is not None:
                self.validate_list_types(attachments)

        if email_to is None:
            email_to = [name for name, address in settings.ADMINS]

        if Notification.objects.filter(pk=notification_pk).exists():
            self.notification_pk = notification_pk
            self.obj = Notification.objects.get(pk=self.notification_pk)
            subject = self.obj.rule_msg
            message = self.obj.message
            if email_type == 0:
                email_to = self.obj.subscribers
            elif email_type == 1: # escalation
                email_to = self.obj.escalation_subscribers
            elif email_type == 2: # both esc, and broadcast
                email_to.extend(
                    self.obj.subscribers).extend(
                        self.obj.escalation)
            else: # error
                raise Exception('Invalid  data %s', 'email_type')
        else:
            raise Exception('Invalid  data %s', 'email_type')

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

    def update_notification_timestamps(self):
        """
        extend this to include the whole send and update logic
        update notification columns upon successful email sent
        days, seconds = duration.days, duration.seconds
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = (seconds % 60)
        return days, hours, minutes, seconds
        """
        Notification.objects.filter(pk=self.notification_pk).update(
            broadcast_on=timezone.now())
        # we need to update escalated_on if no one paid
        #attension to email within
        # timezone.timedelta(instance.notification_type.escalate_within)


        # Notification.objects.filter(pk=self.notification_pk).update(
        #     escalated_on=timezone.now() +
        #     timezone.timedelta(instance.notification_type.escalate_within))
    def validate_list_types(self, items):
        """
        validates if arguments are list instance
        """
        for item in items:
            if not isinstance(item, (list, tuple)):
                raise Exception(str(item) + ": Not a list instance")

    def validate_email_types(self, email_to):
        """
        validates if argument are email format
        """
        if not isinstance(email_to, (list, tuple)):
            raise Exception(str(email_to) + ": Not a list instance")
        elif len(email_to) == 0:
            raise Exception(str(email_to) + ": Invalid Email")
        else:
            for email in email_to:
                try:
                    validate_email(email)
                except ValidationError:
                    raise Exception(str(email) + ": Invalid Email")
