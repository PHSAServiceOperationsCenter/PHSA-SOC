"""
.. _ssl_lib:

:ref:`SSL Certificate Tracker Application` Library
--------------------------------------------------

This module contains classes and functions used by other modules in the
application.

:module:    ssl_certificates.lib

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

:updated:    Dec 16, 2019

"""
from enum import Enum
from logging import getLogger
from smtplib import SMTPConnectError
import socket

from django.conf import settings
from django.db.models import (
    Case, When, CharField, BigIntegerField, Value, F, Func, TextField,
)
from django.db.models.functions import Now, Cast, Concat
from django.utils import timezone
from djqscsv import write_csv
from templated_email import get_templated_mail

from citrus_borg.dynamic_preferences_registry import get_preference, \
    get_list_preference
from p_soc_auto_base import utils

LOG = getLogger(__name__)
"""
fall-back :class:`logging.Logger` object

If any class or function needs a :class:`logging.Logger` object and if one is
**not** provided by the caller, then this :class:`logging.Logger` object will be
used.
"""


class State(Enum):
    """
    Enumeration class for state control attributes
    """
    VALID = 'valid'
    EXPIRED = 'expired'
    NOT_YET_VALID = 'not yet valid'


CASE_EXPIRED = When(not_after__lt=timezone.now(), then=Value(State.EXPIRED))
"""
a representation of an SQL WHEN snippet using :class:`django.db.models.When`

See `Django Conditional Expressions <https://docs.djangoproject.com/en/2.2/ref/models/conditional-expressions/#conditional-expressions>`__
for detail about :class:`django.db.models.Case` and :class:`django.db.models.When`.

In this particular case, if the value of
:attr:`ssl_cert_tracker.models.SslCertificate.not_after` is less than the current
moment, the `SSL` certificate is expired.
"""


CASE_NOT_YET_VALID = When(not_before__gt=timezone.now(),
                          then=Value(State.NOT_YET_VALID))
"""
a representation of an SQL WHEN snippet using :class:`django.db.models.When`

See `Django Conditional Expressions
<https://docs.djangoproject.com/en/2.2/ref/models/conditional-expressions/#conditional-expressions>`__
for detail about :class:`django.db.models.Case` and :class:`django.db.models.When`.

In this particular case, if the value of
:attr:`ssl_cert_tracker.models.SslCertificate.not_before` is greater than the
current moment, the `SSL` certificate is not yet valid.
"""

STATE_FIELD = Case(
    CASE_EXPIRED, CASE_NOT_YET_VALID, default=Value(State.VALID),
    output_field=CharField())
"""
a representation of an SQL CASE snippet using the SQL WHEN snippets from above

See `Django Conditional Expressions
<https://docs.djangoproject.com/en/2.2/ref/models/conditional-expressions/#conditional-expressions>`__
for detail about :class:`django.db.models.When` and :class:`django.db.models.When`.

In this particular case, we are tracking the `STATE` of the
:class:`ssl_cert_tracker.models.SslCertificate` instance with regards to validity
and expiration dates. The possible cases are:

* :attr:`State.NOT_YET_VALID` (not yet valid)

* :attr:`State.VALID` (the default state)

* :attr:`State.EXPIRED`

"""


class DateDiff(Func):  # pylint: disable=abstract-method
    """
    Subclass of the `Django` :class:`django.db.models.Func` class; used as a
    wrapper for the `MariaDB` `DATEDIFF()
    <https://mariadb.com/kb/en/library/datediff/>`__

    See `Func() expressions
    <https://docs.djangoproject.com/en/2.2/ref/models/expressions/#func-expressions>`__
    in the `Django` docs for more details about wrappers for functions provided
    by the database server.

    We are using the database function for `date` arithmetic in order to avoid
    conversion errors that cannot be caught and handled at the `Django` level.

    For some un-blessed reason, the `DATEDIFF()` function returns  a string.
    If one wants to use the values returned by `DATEDIFF()` for sorting, one
    will have to worry about the sort order between `strings` and `numbers`.
    """
    function = 'DATEDIFF'
    output_field = CharField()


def is_not_trusted(app_label='ssl_cert_tracker', model_name='sslcertificate'):
    """
    :returns:

        a :class:`django.db.models.query.QuerySet` based on the
        :class:`ssl_cert_tracker.models.SslCertificate` filtered on the
        `untrusted` state of each `SSL` certificate in
        the :class:`django.db.models.query.QuerySet`

        The :class:`django.db.models.query.QuerySet` will include a calculated
        field that highlights the `untrusted` state of each `SSL` certificate.

        Observe the  `annotated
        <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
        `alert_body` field used as an argument for the
        :meth:`django.db.models.query.QuerySet.annotate` method of the
        :class:`django.db.models.query.QuerySet`.

    :rtype: :class:`django.db.models.query.QuerySet`

    The arguments for this function have not been hard-coded because we want to
    be able to reuse the function even if :mod:`ssl_cert_tracker.models` changes.

    :arg str app_label:

    :arg str model_name:

    """
    return get_ssl_base_queryset(app_label, model_name).\
        filter(issuer__is_trusted=False).\
        annotate(alert_body=Value('Untrusted SSL Certificate',
                                  output_field=TextField()))


def get_ssl_base_queryset(app_label, model_name, url_annotate=True,
                          issuer_url_annotate=True):
    """
    :returns:

        a :class:`django.db.models.query.QuerySet` based on the
        :class:`ssl_cert_tracker.models.SslCertificate` and `annotated
        <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
        with the absolute path of the `URL` for the
        :class:`Django admin <django.contrib.admin.ModelAdmin>` instance based on
        the related entry in :class:`ssl_cert_tracker.models.SslCertificateIssuer`

        The annotation is present in a field named `url_issuer`.

    This function cannot be abstracted to generate annotations for one or more
    foreign key fields  because the `annotation` names cannot be passed as
    variables

    :arg str app_label:

    :arg str model_name:

    :arg bool url_annotate:

    :arg bool issuer_url_annotate:

    """
    queryset = utils.get_base_queryset(f'{app_label}.{model_name}',
                                       enabled=True)
    if url_annotate:
        queryset = utils.url_annotate(queryset)
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
               lt_days=None):
    """
    :returns:

        a :class:`django.db.models.query.QuerySet` based on the
        :class:`ssl_cert_tracker.models.SslCertificate`

        The :class:`django.db.models.query.QuerySet` returned by this function is:

        * `filtered
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#filter>`__
          to show only the :attr:`State.VALID` `SSL` certificates

        * optionally `filtered
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#filter>`__
          for the interval before the `SSL` certificates will expire

          Note that the parameter for this filter is measured in `days` and
          cannot be smaller than 2.

          If this `filter
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#filter>`__
          is applied, the :class:`django.db.models.query.QuerySet` will be
          `annotated
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
          with the value of the parameter in a field named `expires_in_less_than`,
          and with a field named `alert_body` that contains a corresponding
          alert message

        * `annotated
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
          with the :attr:`STATE_FIELD` in a field named `state`, and a
          :class:`django.db.models.BigIntegerField` field named `expires_in_x_days`

        * ordered ascending on the `expires_in_x_days` field

    :arg str app_label:

    :arg str model_name:

    :arg int lt_days:

        filter by the number of days remaining until the `SSL` certificate
        expires

        If less than 2, set to 2.

    """
    if lt_days and lt_days < 2:
        LOG.warning('expiring in less than 2 days is not supported.'
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
    :returns:

        a :class:`django.db.models.query.QuerySet` based on the
        :class:`ssl_cert_tracker.models.SslCertificate`

        The :class:`django.db.models.query.QuerySet` returned by this
        function is:

        * `filtered
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#filter>`__
          to show only the :attr:`State.EXPIRED` `SSL` certificates

        * `annotated
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
          with the :attr:`STATE_FIELD` in a field named `state`, and a
          :class:`django.db.models.BigIntegerField` field named
          `has_expired_x_days_ago`

        * ordered descending on the `has_expired_x_days_ago` field

    :arg str app_label:

    :arg str model_name:

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
    :returns:

        a :class:`django.db.models.query.QuerySet` based on the
        :class:`ssl_cert_tracker.models.SslCertificate`

        The :class:`django.db.models.query.QuerySet` returned by this function is:

        * `filtered
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#filter>`__
          to show only the :attr:`State.NOT_YET_VALID` `SSL` certificates

        * `annotated
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
          with the :attr:`STATE_FIELD` in a field named `state`, and a
          :class:`django.db.models.BigIntegerField` field named
          'will_become_valid_in_x_days'

        * ordered descending on the 'will_become_valid_in_x_days' field

    :arg str app_label:

    :arg str model_name:

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
    Subclass of :class:`django.core.mail.EmailMultiAlternatives`; (see `Sending
    alternative content types
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

    def _debug_init(self):
        """
        dump all the info about the email before actually creating the
        email object
        """
        LOG.debug('headers: %s', self.headers)
        if self.prepared_data:
            LOG.debug('data sample: %s', self.prepared_data[0])
        else:
            LOG.debug('no data')

        context_for_log = dict(self.context)
        context_for_log.pop('headers', None)
        context_for_log.pop('data', None)

        LOG.debug('context: %s', context_for_log)

    def _get_headers_with_titles(self):
        """
        prepares the headers for the columns that will be rendered in the email
        message body

        This method will infer the column names from the field names stored
        under the :attr:`ssl_cert_tracker.models.Subscription.headers` field.
        The method assumes that the field names in the :attr:`headers
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
        create the column name by replacing "__" with ": ". If there are "_"
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
        :attr:`Email.subscription_obj` instance member with a time stamp.
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

        LOG.debug('attachment %s ready', filename)

        self.csv_file = filename

    def __init__(self, data=None, subscription_obj=None, add_csv=True,
                 **extra_context):
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
        :class:`str` attribute for the name of the comma-separated file

        This attribute is set in the :meth:`prepare_csv`.
        """

        if data is None:
            LOG.error('no data was provided for the email')
            raise NoDataEmailError('no data was provided for the email')

        self.data = data
        """
        :class:`django.db.models.query.QuerySet` with the data to be rendered
        in the email message body
        """
        if subscription_obj is None:
            LOG.error('no subscription was provided for the email')
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
        :class:`list` of :class:`dictionaries <dict>` where each item
        represents a row in the :attr:`Email.data`
        :class:`django.db.models.query.QuerySet` with the human readable
        format of the field name (as represented by the values in the
        :attr:`Email.headers` :class:`dictionary <dict>`) as the key and
        the contents of the field as values

        For example, if the `queryset` has one entry with
        dog_name: 'jimmy', the corresponding entry in
        :attr:`Email.headers` is {'dog_name': 'Dog name'}, and the item
        in this list will end up as {'Dog name': 'jimmy'}.
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

        self._debug_init()

        try:
            self.email = get_templated_mail(
                template_name=subscription_obj.template_name,
                template_dir=subscription_obj.template_dir,
                template_prefix=subscription_obj.template_prefix,
                from_email=get_preference('emailprefs__from_email')
                if settings.DEBUG else subscription_obj.from_email,
                to=get_list_preference('emailprefs__to_emails')
                if settings.DEBUG
                else subscription_obj.emails_list.split(','),
                context=self.context, create_link=True)
            LOG.debug('email object is ready')
        except Exception as err:
            LOG.error(str(err))
            raise err

        if self.csv_file:
            self.email.attach_file(self.csv_file)

    def set_tags(self):
        """
        format the contents of the
        :attr:`ssl_cert_tracker.models.Subscription.tags` of the
        :attr:`Email.subscription_obj` to something like "[TAG1][TAG2]etc".

        By convention, the :attr:`ssl_cert_tracker.models.Subscription.tags`
        value is a list of comma separated words or phrases. This method
        converts that value to [TAGS][][], etc.
        A tag containing the hostname of the :ref:`SOC Automation Server` host
        will show as a [$hostname] tag to help with identifying the source of
        the email message.

        In a `DEBUG` environment, this method will prefix all the other tags
        with a [DEBUG] tag. A `DEBUG` environment is characterized by the
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
            LOG.error(str(err))
            raise err
        except Exception as err:
            LOG.error(str(err))
            raise err

        LOG.debug('sent email with subject %s', self.email.subject)

        return sent
