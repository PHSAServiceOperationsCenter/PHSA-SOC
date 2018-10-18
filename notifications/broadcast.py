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


class Error(Exception):
    """Base class for other exceptions"""
    pass

class InputError(Error):
   """Raised when parameter is not valid"""
   pass

class EmailBroadCast(EmailMessage):
    """
    Send an email to a recipient

    :param str subject: email subject
    :param str message: The body of the message
    :param str email_from: email_from
    :param str message: The body of the message
    :param list/tuple email_to: email recepients
    :param list/tuple cc:  email cc
    :param list/tuple bcc: email bcc
    :param obj connection: email connection
    :param list/tuple attachments: email attachments
    :param list/tuple reply_to: email response recepients
    :param dict headers:Extra headers to put on the message
    :param int notification_pk: valid pk if not None.
    :param int email_type: 0:subscribers, 
                           1:esc., 
                           2: sub & esc., 
                           otherwise:subscribers
    :param list/tuple args: TBD
    :param dict kwargs: TBD
    """


    def __init__(self,
                 subject=None,
                 message=None,
                 email_from=settings.ADMINS[0][1],
                 email_to=None,
                 cc=settings.DEFAULT_EMAIL_CC,
                 bcc=settings.DEFAULT_EMAIL_BCC,
                 connection=None,
                 attachments=None,
                 reply_to=settings.DEFAULT_EMAIL_REPLY_TO,
                 headers=settings.DEFAULT_EMAIL_HEADERS,
                 notification_pk=settings.DEFAULT_NOTIFICATION_PK,
                 email_type=settings.SUB_EMAIL_TYPE,
                 *args,
                 **kwargs
                ):

        """
        Initialize class parameters and invalid format
        """
        self.obj = None

        if email_to is None:
            email_to = [name for name, address in settings.ADMINS]

        if notification_pk is None:
            if subject is None or message is None:
                raise InputError("Email Subject/Message")

        try:
            validate_email(email_from)
        except ValidationError:
            raise InputError("Invalid Email From")

        self.validate_email_types(email_to)
        self.validate_list_types([cc, bcc])
        self.validate_email_types(reply_to)
        if attachments is not None:
            self.validate_list_types(attachments)

        if Notification.objects.filter(pk=notification_pk).exists():
            self.notification_pk = notification_pk
            self.obj = Notification.objects.get(pk=notification_pk)
            subject = self.obj.rule_msg
            message = self.obj.message
            if email_type == settings.SUB_EMAIL_TYPE:
                email_to = self.obj.subscribers
            elif email_type == settings.ESC_EMAIL_TYPE: # escalation
                email_to = self.obj.escalation_subscribers
            elif email_type == settings.SUB_ESC_EMAIL_TYPE: # both esc, and broadcast
                email_to.extend(
                    self.obj.subscribers).extend(
                        self.obj.escalation)
            else: # error
                raise InputError('Invalid  data %s', 'email_type')
        else:
            raise InputError('Invalid  data %s', 'email_type')


        

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
                raise InputError(str(item) + ": Not a list instance")

    def validate_email_types(self, email_to):
        """
        validates if argument are email format
        """
        if not isinstance(email_to, (list, tuple)):
            raise InputError(str(email_to) + ": Not a list instance")
        elif len(email_to) == 0:
            raise InputError(str(email_to) + ": Invalid Email")
        else:
            for email in email_to:
                try:
                    validate_email(email)
                except ValidationError:
                    raise InputError(str(email) + ": Invalid Email")
