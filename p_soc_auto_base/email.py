"""
..email:

Email module
------------

This module contains classes and functions used by other modules in the
application to send email alerts.

:module:    p_soc_auto_base.email

:copyright:

    Copyright 2020- Provincial Health Service Authority of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from logging import getLogger
from smtplib import SMTPConnectError
import socket

from django.conf import settings
from django.utils import timezone
from djqscsv import write_csv
from templated_email import get_templated_mail

from citrus_borg.dynamic_preferences_registry import get_preference, \
    get_list_preference

LOG = getLogger(__name__)


class Email:
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
    def __init__(self, data, subscription_obj, add_csv=True,
                 **extra_context):
        """
        :arg data: a :class:`django.db.models.query.QuerySet`

        :arg subscription_obj: :class:`p_soc_auto_base.models.Subscription`
            instance

            Will contain all the metadata required to build and send the email
            message. This includes template information and pure SMTP data
            (like email addresses and stuff).

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

        self.subscription_obj = subscription_obj
        """
        an :class:`p_soc_auto_base.models.Subscriptions` instance with the
        details required for rendering and sending the email message
        """

        self.data = data
        """
        :class:`django.db.models.query.QuerySet` with the data to be rendered
        in the email message body
        """

        self.headers = self._get_headers_with_titles()
        """
        a :class:`dictionary <dict>` that maps human readable column names
        (headers) to the fields in the :attr:`data`
        :class:`django.db.models.query.QuerySet`
        """

        self._prepare_csv()

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

        if data:
            self.prepared_data = [
                {key: data_item[key] for key in self.headers.keys()}
                for data_item in data.values(*self.headers.keys())
            ]

        self.context = dict(
            report_date_time=timezone.now(),
            headers=self.headers, data=self.prepared_data,
            source_host_name='http://%s:%s' % (socket.getfqdn(),
                                               settings.SERVER_PORT),
            source_host=socket.getfqdn(),
            tags=self._set_tags(),
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

        LOG.debug('Context: %s', self.context)

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
            LOG.exception(str(err))
            raise err

        if self.csv_file:
            self.email.attach_file(self.csv_file)

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
        under the :attr:`p_soc_auto_base.models.Subscription.headers` field.
        The method assumes that the field names in the :attr:`headers
        <p_soc_auto_base.models.Subscription.headers>` field will match field
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
            names from :attr:`p_soc_auto_base.models.Subscription.headers`
            and the values are created using the rules above

        """
        if not self.data:
            return {}

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

    def _prepare_csv(self):
        """
        generate a comma-separated file with the values in the
        :attr:`Email.data` if required via the :attr:`Email.add_csv` attribute
        value

        If the :attr:`data` is empty, the comma-separated file will not be
        created.

        The file will be named by linking the value of the :attr:`email subject
        <p_soc_auto_base.models.Subscription.email_subject> attribute of the
        :attr:`Email.subscription` instance member with a time stamp.
        The file will be saved under the path described by
        :attr:`p_soc_auto.settings.CSV_MEDIA_ROOT`.
        """
        if not self.add_csv or not self.data:
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

    def _set_tags(self):
        """
        format the contents of the
        :attr:`p_soc_auto_base.models.Subscription.tags` of the
        :attr:`Email.subscription` to something like "[TAG1][TAG2]etc".

        By convention, the :attr:`p_soc_auto_base.models.Subscription.tags`
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

        LOG.debug('tags are %s', tags)
        return tags

    def _send(self):
        try:
            sent = self.email.send()
        except SMTPConnectError as err:
            LOG.exception(str(err))
            raise err
        except Exception as err:
            LOG.exception(str(err))
            raise err

        LOG.debug('sent email with subject %s', self.email.subject)

        return sent

    @classmethod
    def send_email(cls, data, subscription, add_csv=True, **extra_context):
        """
        send an email message

        :arg data: a :class:`Django queryset <django.db.models.query.QuerySet>`

        :arg str subscription: the key for retrieving the :class:`Subscription
            <p_soc_auto_base.models.Subscription>` instance that will be used
            for rendering and addressing the email

        :arg bool add_csv: attach a csv file with the contents of the `data`
            argument to the email; default is `True`

        :arg dict extra_context: optional arguments with additional data to be
            rendered in the email

            .. note::

                Do not use `data`, `subscription`, `add_csv`, or `extra_content`
                as names for email data elements as they will be interpreted as
                other arguments of this function (causing unexpected behaviour)
                or cause an exception.

        :returns: '1' if the email message was sent, and '0' if not
        """
        return cls(data, subscription, add_csv, **extra_context)._send()
