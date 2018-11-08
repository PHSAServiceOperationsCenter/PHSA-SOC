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
import json

from django.conf import settings
from django.core.exceptions import MultipleObjectsReturned, ObjectDoesNotExist
from django.core.exceptions import ValidationError
from django.core.mail.message import EmailMessage
from django.core.validators import validate_email
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from ssl_cert_tracker.models import NmapCertsData

from .models import Notification


class Error(Exception):
    """Base class for other exceptions"""
    pass


class InputError(Error):
    """Raised when parameter is not valid"""
    pass


class EmailBroadCast(EmailMessage):
    """
    email broadcast class

    drop in replacement for `djang.core.mail.EmailMessage' that also can
    take a notification obkect and create an email message out of it
    """

    def __init__(
            self, notification_pk=None, subject=None, message=None,
            email_from=settings.ADMINS[0][1], email_to=None, cc=None, bcc=None,
            connection=None, attachments=None,
            reply_to=settings.DEFAULT_EMAIL_REPLY_TO, headers=None,
            email_type=settings.SUB_EMAIL_TYPE, *args, **kwargs):
        """
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
        """
        self.obj = None
        if email_to is None:
            email_to = [address for name, address in settings.ADMINS]

        if notification_pk is None:
            if subject is None or message is None:
                raise InputError("Email Subject/Message")

        try:
            validate_email(email_from)
        except ValidationError:
            raise InputError("Invalid Email From")

        self.validate_email_types(email_to)
        self.validate_email_types(reply_to)
        if attachments is not None:
            self.validate_list_types(attachments)

        if Notification.objects.filter(pk=notification_pk).exists():
            self.notification_pk = notification_pk
            self.obj = Notification.objects.get(pk=notification_pk)
            subject, message = format_email_subject_message(self.obj)
            if email_type == settings.SUB_EMAIL_TYPE:
                email_to = self.obj.subscribers
            elif email_type == settings.ESC_EMAIL_TYPE:
                email_to = self.obj.escalation_subscribers
            elif email_type == settings.SUB_ESC_EMAIL_TYPE:
                email_to.\
                    extend(self.obj.subscribers).\
                    extend(self.obj.escalation_subscribers)
            else:  # error
                raise InputError('Invalid  data %s' % 'email_type')

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
        # attension to email within
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
                raise InputError(str(item) % (": Not a list instance"))

    def validate_email_types(self, email_to):
        """
        validates if argument are email format
        """
        if not isinstance(email_to, (list, tuple)):
            raise InputError(str(email_to) % (": Not a list instance"))
        elif not email_to:
            raise InputError(str(email_to) % (": Invalid Email"))
        else:
            for email in email_to:
                try:
                    validate_email(email)
                except ValidationError:
                    raise InputError(str(email) % (": Invalid Email"))


def format_email_subject_message(notification_obj):
    """
    Get ssl_cert object from notification object
    """
    if notification_obj.rule_applies.content_type.model in ['nmapcertsdata']:
        try:
            # ssl_notifications = notification_obj.objects.filter(
            #    rule_applies__content_type__model__iexact='nmapcertsdata')
            ssl_object = NmapCertsData.objects.get(
                id=notification_obj.instance_pk)
            subject, message_text = ssl_cert_display_fields(ssl_object,
                                                            notification_obj)
        except MultipleObjectsReturned as ex:
            # Serban Do we need to grab the firs() here or
            # raise error as it is now
            raise InputError("more than one object found %s" % (str(ex)))

        except ObjectDoesNotExist as ex:
            raise InputError("Object does not exist %s" % (str(ex)))
    else:
        raise InputError("not yet implemented")

    return subject, message_text


def ssl_cert_display_fields(cert_instance, noti_instance):
    """
    ssl_cert_display_fields message
    """
    noti_rule_msg = json.loads(noti_instance.rule_msg)
    relationship = str(noti_rule_msg["relationship"])
    subject_type = relationship. \
        replace(" ", ""). \
        replace("\r", ""). \
        replace("\n", ""). \
        replace("\t", ""). \
        lower()

    rule_action = {
        "notyetvali": not_yet_valid(cert_instance, noti_rule_msg),
        "willexpire": will_expire_in_less_than(cert_instance, noti_rule_msg),
        "hasexpired": has_expired(cert_instance, noti_rule_msg)
    }
    subject, message = rule_action.get(subject_type[0:10],
                                       "not yet implemented")
    return subject, message


def will_expire_in_less_than(cert_instance, noti_rule_msg):
    """
    This relationship build message for will exopir...rule
    """
    subject_list = []

    days = str(noti_rule_msg["grace_period"]["days"])
    relationship = str(noti_rule_msg["relationship"])

    subject_list.append("Alert - An SSL certificate on ")
    subject_list.append(" %s " % (str(cert_instance.common_name)))
    subject_list.append("on port 443 will Expire in %s days" % (days))

    subject = " ".join(map(str, subject_list))
    message = generate_ssl_cert_message(cert_instance,
                                        noti_rule_msg,
                                        True)
    return subject, message


def not_yet_valid(cert_instance, noti_rule_msg):
    """
    This relationship build message for not_yet_valid...rule
    """
    subject_list = []

    relationship = str(noti_rule_msg["relationship"])

    subject_list.append("Alert - An SSL certificate on ")
    subject_list.append(" %s " % (str(cert_instance.common_name)))
    subject_list.append("on port 443 invalid due to %s" % (relationship))

    subject = " ".join(map(str, subject_list))
    message = generate_ssl_cert_message(cert_instance,
                                        noti_rule_msg
                                        )
    return subject, message


def has_expired(cert_instance, noti_rule_msg):
    """
    This relationship build message for has_expired...rule
    """

    subject_list = []

    not_after = str(parse_datetime(noti_rule_msg["facts"][1])).split()[0]
    relationship = str(noti_rule_msg["relationship"])

    subject_list.append("Alert - An SSL certificate on ")
    subject_list.append(" %s " % (str(cert_instance.common_name)))
    subject_list.append("on port 443 has expired on %s" % not_after)

    subject = " ".join(map(str, subject_list))
    message = generate_ssl_cert_message(cert_instance,
                                        noti_rule_msg)

    return subject, message


def generate_ssl_cert_message(cert_instance, noti_rule_msg, grace_period=False):
    """
    Generate message for ssl-cert email
    """

    msg_list = []
    host_name = str(cert_instance.common_name)
    not_valid_before = str(parse_datetime(
        str(cert_instance.not_before))).split()[0]

    not_valid_after = str(parse_datetime(
        str(cert_instance.not_after))).split()[0]

    days = noti_rule_msg["grace_period"]["days"]
    relationship = str(noti_rule_msg["relationship"])

    msg_list.append("\nHost Name: %s" % (host_name))
    msg_list.append("\nNot_valid_before: %s" % (not_valid_before))
    msg_list.append("\nNot_valid_after: %s" % (not_valid_after))
    msg_list.append("\n\nIssuer Info")
    msg_list.append("\n\tOrginization_unit_name: %s" % ("Place Holder"))
    msg_list.append("\n\tOrginization_name: %s" %
                    (str(cert_instance.organization_name)))
    msg_list.append("\n\tCountry_name: %s" %
                    (str(cert_instance.country_name)))
    msg_list.append("\n\tCommon_name: %s" % (str(cert_instance.common_name)))

    if grace_period:
        msg_list.append("\nCertificate Alert Threshold: %s" %
                        (str(noti_rule_msg["now"])))
        msg_list.append("\n\nNotification Cause: %s" % (relationship))
        msg_list.append("\n\nGrace Period:")
        msg_list.append("\n\tDays: %s" % (days))

    msg_list.append("\n\nDiagnostics:")
    msg_list.append("\n\t %s" % (str(noti_rule_msg)))

    message = " ".join(map(str, msg_list))
    return message
