"""
.. _lib:

library module for the ssl_certificates app

:module:    ssl_certificates.lib

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Oct. 30, 2018

"""
from enum import Enum
from logging import getLogger
from smtplib import SMTPConnectError
import socket

from django.apps import apps
from django.conf import settings
from django.db.models import (
    Case, When, CharField, BigIntegerField, Value, F, Func, TextField,
)
from django.db.models.functions import Now, Cast, Concat
from django.utils import timezone
from djqscsv import write_csv
from templated_email import get_templated_mail

from citrus_borg.dynamic_preferences_registry import get_preference


LOG = getLogger('ssl_cert_tracker')


class State(Enum):
    """
    enumeration for state values
    """
    VALID = 'valid'
    EXPIRED = 'expired'
    NOT_YET_VALID = 'not yet valid'


CASE_EXPIRED = When(not_after__lt=timezone.now(), then=Value(State.EXPIRED))
"""
:var CASE_EXPIRED:

    a representation of an SQL WHEN snippet looking for certificates
    that have expired already

:vartype: :class:`<django.db.models.When>`
"""


CASE_NOT_YET_VALID = When(not_before__gt=timezone.now(),
                          then=Value(State.NOT_YET_VALID))
"""
:var CASE_NOT_YET_VALID: a representation of an SQL WHEN snippet looking for
                    certificates that are not yet valid

:vartype: :class:`<django.db.models.When>`
"""

STATE_FIELD = Case(
    CASE_EXPIRED, CASE_NOT_YET_VALID, default=Value(State.VALID),
    output_field=CharField())
"""
:var STATE_FIELD: a representation of an SQL CASE snipped that used the
                  WHEN snippetys from above to categorize SSL certificates by
                  their validity state

:vartype: :class:`<django.db.models.Case>`
"""


class DateDiff(Func):  # pylint: disable=abstract-method
    """
    django wrapper for the MariaDB function DATEDIFF(). see

    `<https://mariadb.com/kb/en/library/datediff/>`_

    need to use the database function to avoid uncaught conversion errors

    the DATEDIFF() function returns for some un-blessed reason a string so we
    need to use a char field which will impose another annotation to
    convert the result to ints for sorting purposes
    """
    function = 'DATEDIFF'
    output_field = CharField()


def is_not_trusted(app_label='ssl_cert_tracker', model_name='sslcertificate'):
    """
    get untrusted certificates

    the arguments are required because this and the other queryset returning
    functions in this module are written so that we can pull data from either
    the old certificate model or the new, refoctored certificate models.

    :arg str app_label:

    :arg str model_name:
    """
    return get_ssl_base_queryset(app_label, model_name).\
        filter(issuer__is_trusted=False).\
        annotate(alert_body=Value('Untrusted SSL Certificate',
                                  output_field=TextField()))


def get_base_queryset(app_label, model_name, url_annotate=True):
    """
    get a basic queryset object and also annotate with the absolute
    django admin change URL

    :arg str app_label:

    :arg str model_name:

    :returns:

        a django queryset that includes a field named 'url' containing
        tbe absolute URL for the django admin change page associated with
        the row
    """
    queryset = apps.get_model(app_label,
                              model_name).objects.filter(enabled=True)

    if url_annotate:
        queryset = queryset.annotate(url_id=Cast('id', TextField())).\
            annotate(url=Concat(
                Value(settings.SERVER_PROTO), Value('://'),
                Value(socket.getfqdn()),
                Value(':'), Value(settings.SERVER_PORT),
                Value('/admin/'),
                Value(app_label), Value('/'), Value(model_name),
                Value('/'), F('url_id'), Value('/change/'),
                output_field=TextField()))

    return queryset


def get_ssl_base_queryset(
        app_label, model_name, url_annotate=True, issuer_url_annotate=True):
    """
    annotate with the absolute url to the certificate issuer row

    we put this in a separate function because get_base_queryset is
    supposed to be pristine with no dependencies to any specific model
    whatsoever

    this cannot be abstracted to generate annotations for each
    foreign key field  because the annotation name cannot be passed as
    a variable
    """
    queryset = get_base_queryset(app_label, model_name, url_annotate)
    if issuer_url_annotate \
            and app_label in ['ssl_cert_tracker'] \
            and model_name in ['sslcertificate']:
        queryset = queryset.\
            annotate(url_issuer_id=Cast('issuer__id', TextField())).\
            annotate(url_issuer=Concat(
                Value(settings.SERVER_PROTO), Value('://'),
                Value(socket.getfqdn()),
                Value(':'), Value(settings.SERVER_PORT),
                Value('/admin/'),
                Value(app_label), Value('/sslcertificateissuer/'),
                F('url_issuer_id'), Value('/change/'),
                output_field=TextField()))

    return queryset


def expires_in(app_label='ssl_cert_tracker', model_name='sslcertificate',
               lt_days=None, logger=None):
    """
    annotation function that prepares a query with calculated values

    the SQL equivalent is something along the lines of
    SELECT DATEDIFF(not_after, NOW()) AS expires_in_x_days FROM table WHERE
    state = 'valid' ORDER BY expires_in_x_days;

    :returns: a django queryset that has access to all the field in
              NmapCertData plus a state field, an expires_in_x_days field, and
              a field with the value returned by the MySql SQL function NOW()
    """
    if logger is None:
        logger = LOG

    if lt_days and lt_days < 2:
        logger.warning('expiring in less than 2 days is not supported.'
                       ' resetting lt_days=%s to 2', lt_days)
        lt_days = 2

    queryset = get_ssl_base_queryset(app_label, model_name).\
        annotate(state=STATE_FIELD).filter(state=State.VALID).\
        annotate(mysql_now=Now()).\
        annotate(expires_in=DateDiff(F('not_after'), F('mysql_now'))).\
        annotate(expires_in_x_days=Cast('expires_in', BigIntegerField()))

    if lt_days:
        queryset = queryset.\
            annotate(expires_in_less_than=Value(lt_days, BigIntegerField())).\
            annotate(expires_in_less_than_cast=Cast(
                'expires_in_less_than', CharField())).\
            annotate(alert_body=Concat(
                Value(
                    'SSL Certificate will expire in less than ', TextField()),
                F('expires_in_less_than_cast'),
                Value(' days', TextField()), output_field=TextField())).\
            filter(expires_in_x_days__lt=lt_days)

    queryset = queryset.order_by('expires_in_x_days')

    return queryset


def has_expired(app_label='ssl_cert_tracker', model_name='sslcertificate'):
    """
    annotation function that returns data calculated at the database level
    for expired certificates

    :returns: a django queryset
    """
    queryset = get_ssl_base_queryset(app_label, model_name).\
        annotate(state=STATE_FIELD).filter(state=State.EXPIRED).\
        annotate(mysql_now=Now()).\
        annotate(has_expired_x_days_ago=DateDiff(F('mysql_now'),
                                                 F('not_after'))).\
        annotate(has_expired_x_days_ago_cast=Cast('has_expired_x_days_ago',
                                                  CharField())).\
        annotate(alert_body=Concat(
            Value('SSL Certificate has expired ', TextField()),
            F('has_expired_x_days_ago_cast'),
            Value(' days ago', TextField()), output_field=TextField())).\
        order_by('-has_expired_x_days_ago')

    return queryset


def is_not_yet_valid(
        app_label='ssl_cert_tracker', model_name='sslcertificate'):
    """
    annotation function that returns data calculated at the database level
    for certificates that are not yet valid

    :returns: a django queryset
    """
    queryset = get_ssl_base_queryset(app_label, model_name).\
        annotate(state=STATE_FIELD).filter(state=State.NOT_YET_VALID).\
        annotate(mysql_now=Now()).\
        annotate(will_become_valid_in_x_days=DateDiff(
            F('not_before'), F('mysql_now'))).\
        annotate(will_become_valid_in_x_days_cast=Cast(
            'will_become_valid_in_x_days', CharField())).\
        annotate(alert_body=Concat(
            Value('SSL Certificate will become valid in ', TextField()),
            F('will_become_valid_in_x_days_cast'),
            Value(' days', TextField()), output_field=TextField())).\
        order_by('-will_become_valid_in_x_days')

    return queryset


class NoDataEmailError(Exception):
    """
    raise this if one tries to create an instance of :class:`<Email>` with no
    data
    """


class NoSubscriptionEmailError(Exception):
    """
    raise this if one tries to create an instance of :class:`<Email>` with no
    subscription object
    """


class Email():  # pylint: disable=too-few-public-methods, too-many-instance-attributes
    """
    a (more or less) subclass of
    :class:`<django.core.mail.EmailMultiAlternatives>` with a body prepared
    from django template

    instances of this class are multi-part (test and html) email messages
    """

    def _get_headers_with_titles(self):
        """
        prepare the column heads

        in most cases these can be the model.field.verbose_name properties
        so we look into the model._meta API

        if there is __ we are looking at a relationship. for the moment we
        will just take the substring after the last __ and call it a day

        if we cannot find a field that matches and it is not a relationship,
        it is an annotation and there isn't much we cando; replace _ with
        space and call it a day

        everything will be capitalized using ``str.title()``

        :returns: a ``dict`` that will be part of the template context
        """
        field_names = [
            field.name for field in self.data.model._meta.get_fields()]
        headers = dict()
        for key in self.subscription_obj.headers.split(','):
            if key in field_names:
                headers[key] = self.data.model._meta.get_field(
                    key).verbose_name.title()
            else:
                headers[key] = key.replace(
                    '__', ': ').replace('_', ' ').title()

        return headers

    def prepare_csv(self):
        """
        generate csv file if possible
        """
        if not self.add_csv:
            return

        if not self.data:
            # there is no spoon; don't try to bend it
            return

        filename = 'no_name'
        if self.subscription_obj.email_subject:
            filename = self.subscription_obj.email_subject.\
                replace('in less than', 'soon').\
                replace(' ', '_')

        filename = '{}{:%Y_%m_%d-%H_%M_%S}_{}.csv'.format(
            settings.CSV_MEDIA_ROOT,
            timezone.localtime(value=timezone.now()), filename)

        with open(filename, 'wb') as csv_file:
            write_csv(self.data.values(*self.headers.keys()),
                      csv_file, field_header_map=self.headers)

        self.csv_file = filename

    def __init__(
            self, data=None, subscription_obj=None, logger=None,
            add_csv=True, **extra_context):
        """
        :arg data: a django queryset
                   the constructor will prepare the template context and pass
                   it to the :function:`<templated_email.get_templated_mail>`
                   which is responsible for rendering the subject and body
                   of the email message

        :arg subscription_obj: an instance of
                               :class:`<ssl_cert_tracker.models.Subscription>`
                               containing all the meta-date required to
                               build and send an email message. this includes
                               template information and pure SMTP data (like
                               email addresses and stuff)

        :arg logger: a logging.logger object

        :arg bool add_csv: generate a csv file from :arg data: and
                              attach it to the email. if the file is not
                              generated, log the problem and send the email
                              without attachments

        :arg dict extra_context: just in case one needs more data
        """
        self.add_csv = add_csv
        self.csv_file = None

        if logger is None:
            self.logger = LOG
        else:
            self.logger = logger

        if data is None:
            self.logger.error('no data was provided for the email')
            raise NoDataEmailError('no data was provided for the email')

        self.data = data
        if subscription_obj is None:
            self.logger.error('no subscription was provided for the email')
            raise NoSubscriptionEmailError(
                'no subscription was provided for the email')

        self.subscription_obj = subscription_obj

        self.headers = self._get_headers_with_titles()

        self.prepare_csv()

        self.prepared_data = []
        for data_item in data.values(*self.headers.keys()):
            self.prepared_data.append(
                {key: data_item[key] for key in self.headers.keys()})

        self.context = dict(
            report_date_time=timezone.now(),
            headers=self.headers, data=self.prepared_data,
            source_host_name='http://%s:%s' % (socket.getfqdn(),
                                               settings.SERVER_PORT),
            source_host=socket.getfqdn(),
            tags=self.set_tags(),
            email_subject=self.subscription_obj.email_subject,
            alternate_email_subject=self.subscription_obj.
            alternate_email_subject,
            subscription_name=subscription_obj.subscription,
            subscription_id=subscription_obj.pk)

        if extra_context:
            self.context.update(**extra_context)

        try:
            self.email = get_templated_mail(
                template_name=subscription_obj.template_name,
                template_dir=subscription_obj.template_dir,
                template_prefix=subscription_obj.template_prefix,
                from_email=get_preference('emailprefs__from_email')
                if settings.DEBUG else subscription_obj.from_email,
                to=get_preference('emailprefs__to_emails').split(',')
                if settings.DEBUG
                else subscription_obj.emails_list.split(','),
                context=self.context, create_link=True)
        except Exception as err:
            self.logger.error(str(err))
            raise err

        if self.csv_file:
            self.email.attach_file(self.csv_file)

    def set_tags(self):
        """
        create the values for a {{ tags }} element in the template

        in case we have subscriptions that have a tags attribute (something
        that will happend in uhuru), add all the tags from the
        subscription instance; tags is a CharField and uses comma to
        separate between tags

        we also prefix everything with a [DEBUG] tag if this is a
        DEBUG deployment and we always include a [$host name] tag
        """
        tags = ''

        if self.subscription_obj.tags:
            for tag in self.subscription_obj.tags.split(','):
                tags += '[{}]'.format(tag)

        tags = '[{}]{}'.format(socket.getfqdn(), tags)

        if settings.DEBUG:
            tags = '[DEBUG]{}'.format(tags)

        return tags

    def send(self):
        """
        wrapper around the
        :method:`<django.core.mail.EmailMultiAlternatives.send>`
        """
        try:
            sent = self.email.send()
        except SMTPConnectError as err:
            self.logger.error(str(err))
            raise err
        except Exception as err:
            self.logger.error(str(err))
            raise err

        self.logger.debug(
            'sent email with subject %s and body %s',
            self.email.subject, self.email.body)

        return sent
