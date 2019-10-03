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
    Custom :exc:`Exception` class

    Raise this exception if one tries to create an instance of :class:`Email`
    with a :attr:`Email.data` attribute of :class:`NoneType` (:attr:`data` is ``None``).

    The expectation is that :attr:`Email.data` is a
    :class:`django.db.models.query.QuerySet` and the :class:`Email` class can handle
    empty `QuerySet` objects. This exception prevents invoking the :class:`Email`
    class without a `data` argument in the constructor.
    """


class NoSubscriptionEmailError(Exception):
    """
    Custom :exc:`Exception` class

    Raise this exception if one tries to create an instance of :class:`Email`
    without specifying the `subscription` key for a :class:`Subscription
    <ssl_cert_tracker.models.Subscription>` instance.
    """


class Email():  # pylint: disable=too-few-public-methods, too-many-instance-attributes
    """
    Subclass of
    :class:`django.core.mail.EmailMultiAlternatives`; (see `Sending alternative
    content types
    <https://docs.djangoproject.com/en/2.2/topics/email/#sending-alternative-content-types>`_
    under the `EmailMessage class
    <https://docs.djangoproject.com/en/2.2/topics/email/#the-emailmessage-class>`_
    in the Django docs about `Sending email
    <https://docs.djangoproject.com/en/2.2/topics/email/#module-django.core.mail>`_)

    This class allows for using `Django templates
    <https://docs.djangoproject.com/en/2.2/ref/templates/language/>`_ when
    creating multi-part (text and html) email messages by way of the
    `django-templated-email
    <https://github.com/vintasoftware/django-templated-email>`_ package.

    The class assumes that all email messages are based on tabular data coming
    from the database and they also contain some metadata to make the
    message easier to understand.
    Both the data and the metadata are plugged into a `Django template` using
    a `context
    <https://docs.djangoproject.com/en/2.2/ref/templates/api/#rendering-a-context>`_.

    See :ref:`Email template sample` for an example of a `Django template`
    to be plugged into an instance of this class
    """

    def _get_headers_with_titles(self):
        """
        prepares the headers for the columns that will be rendered in the email
        message body

        This method will infer the column names from the field names stored
        under the :attr:`ssl_cert_tracker.models.Subscription.headers` field.
        The metho assumes that the field names in the :attr:`headers
        <ssl_cert_tracker.models.Subscription.headers>` field will match field
        names in the :attr:`Email.data`
        :class:`queryset <django.db.models.query.QuerySet>`.

        In most cases the field names in a `queryset` are the same as the
        fields in the :class:`django.db.models.Model` that was used to
        construct it. Such fields have a :attr:`verbose_name` attribute that
        is used to provide human readable names for the fields. We retrieve
        the :attr:`verbose_name` for each field using the `Model _meta API
        <https://docs.djangoproject.com/en/2.2/ref/models/meta/#module-django.db.models.options>`_.

        Some field names in the `queryset` will contain one or more occurrences
        of the "__" substring. In this case, the field represents a
        relationship and the relevant `verbose_name` attribute is present in
        a different model. Under the current implementation, this method will
        create the column n by replacing "__" with ": ". If there are "_"
        substrings as well (classic Python convention for attribute names),
        they will be replaced with " ".

        Some fields in the `queryset` are calculated (and created) on the fly
        when the `queryset` is `evaluated
        <https://docs.djangoproject.com/en/2.2/topics/db/queries/#querysets-are-lazy>`_.
        In this case, we cannot make any reasonable guesses about the field
        names, except that they may contain the "_" substring as a
        (convention based) separator. Column headers for these field will be
        based on replacing the "_" occurrences with " " (spaces).

        All column headers are capitalized using :meth:`str.title`.

        :returns: a :class:`dictionary <dict>` in which the keys are the field
            names from :attr:`ssl_cert_tracker.models.Subscription.headers`
            and the values are created using the rules above

        """
        field_names = [
            field.name for field in self.data.model._meta.get_fields()]
        headers = dict()
        for key in self.subscription_obj.headers.split(','):
            if key in field_names:
                headers[key] = self.data.model._meta.get_field(
                    key).verbose_name.title()
            elif '__' in key:
                headers[key] = key.replace(
                    '__', ': ').replace('_', ' ').title()
            else:
                headers[key] = key.replace('_', ' ').title()

        return headers

    def prepare_csv(self):
        """
        generate a comma-separated file with the values in the
        :attr:`Email.data` if required via the :attr:`Email.add_csv` attribute
        value

        If the :attr:`data` is empty, the comma-separated file will not be
        created.

        The file will be named by linking the value of the :attr:`email subject
        <ssl_cert_tracker.models.Subscription.email_subject> attribute of the
        :attr:`Email.subscripttion_obj` instance member with a time stamp.
        The file will be saved under the path described by
        :attr:`p_soc_auto.settings.CSV_MEDIA_ROOT`.
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
        :arg data: a :class:`django.db.models.query.QuerySet`

        :arg subscription_obj: :class:`ssl_cert_tracker.models.Subscription`
            instance

            Will contain all the metadata required to build and send the email
            message. This includes template information and pure SMTP data
            (like email addresses and stuff).

        :arg logger: a :class:`logging.logger` object

            If one is not provided, the constructor will create one

        :arg bool add_csv: generate the csv file from :attr:`Email.data` and
            attach it to the email message?

        :arg dict extra_context: additional data required by the
            `Django template
            <https://docs.djangoproject.com/en/2.2/topics/templates/#module-django.template>`_
            for rendering the email message

            If this argument is present, the {key: value,} pairs therein will
            be appended to the :attr:`Email.context`
            :class:`dictionary <dict>`.

        :raises: :exc:`Exception` if the email message cannot be prepared
        """

        self.add_csv = add_csv
        """
        :class:`bool` attribute controlling whether a comma-separated file is
        to be created and attached to the email message
        """

        self.csv_file = None
        """
        :class:`str` attribute for the name of the comma-separared file

        This attribute is set in the :meth:`prepare_csv`.
        """

        if logger is None:
            self.logger = LOG
            """:class:`logging.Logger` instance"""
        else:
            self.logger = logger
            """:class:`logging.Logger` instance"""

        if data is None:
            self.logger.error('no data was provided for the email')
            raise NoDataEmailError('no data was provided for the email')

        self.data = data
        """
        :class:`django.db.models.query.QuerySet` with the data to be rendered
        in the email message body
        """
        if subscription_obj is None:
            self.logger.error('no subscription was provided for the email')
            raise NoSubscriptionEmailError(
                'no subscription was provided for the email')

        self.subscription_obj = subscription_obj
        """
        an :class:`ssl_cert_tracker.models.Subscriptions` instance with the
        details required for rendering and sending the email message
        """

        self.headers = self._get_headers_with_titles()
        """
        a :class:`dictionary <dict>` that maps human readable column names
        (headers) to the fields in the :attr:`data`
        :class:`django.db.models.query.QuerySet`
        """

        self.prepare_csv()

        self.prepared_data = []
        """
        :class:`lst of :class:`dictionaries <dict>` where each item represents
        a row in the :attr:`Email.data`
        :class:`django.db.models.query.QuerySet` with the human readable format
        of the field name (as represented by the values in the
        :attr:`Email.headers` :class:`dictionary <dict>`) as the key and the
        contents of the field as values

        For example, if the `queryset` has one entry with dog_name: `jimmy`,
        the corresponding entry in :attr:`Email.heasers` is
        {'dog_name': 'Dog name'}, and the item in this list will end up as
        {'Dog name': 'jimmy'}.
        """

        # pylint: disable=consider-iterating-dictionary
        for data_item in data.values(*self.headers.keys()):
            self.prepared_data.append(
                {key: data_item[key] for key in self.headers.keys()})

        # pylint: enable=consider-iterating-dictionary

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
        """
        :class:`dictionary <dict>` used to `render the context
        <https://docs.djangoproject.com/en/2.2/ref/templates/api/#rendering-a-context>`_
        for the email message
        """

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
        format the contents of the
        :attr:`ssl_sert_tracker.models.Subscription.tags` of the
        :attr:`Eamil.subscription_obj` to something like "[TAG`][TAG2]etc"

        By convention, the :attr:`ssl_sert_tracker.models.Subscription.tags`
        value is a list of comma separated words or phrases. This method
        converts that value to [TAGS][][], etc.
        A tag containing the hostname of the :ref:`SOC Automation Server` host
        will show as a [$hostname] tag to help with identifying the source of
        the email message.

        In a `DEBUG` environment, this method will prefix all the other tags
        with a [DEBUG] tag. A `DEBUG` environemnt is characterized by the
        value of :attr:`p_soc_auto.settings.DEBUG`.
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
        send the email message

        wrapper around :meth:`django.core.mail.EmailMultiAlternatives.send`

        :returns: '1' if the email message was sent, and '0' if not

        :raises:

            :exc:`smtplib.SMTPConnectError` if an `SMTP` error is thrown

            :exc:`Exception` if any other errors are thrown

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
