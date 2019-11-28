"""
.. _utils:

:module:    p_soc_auto.p_soc_auto_base.utils

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:update:    Nov. 7, 2019

This module contains utility `Python` classes and functions used by the
`Django` applications  of the :ref:`SOC Automation Server`.

"""
import datetime
import ipaddress
import logging
import socket
import time
import uuid

from django.apps import apps
from django.core.exceptions import FieldError
from django.conf import settings
from django.db.models import F, Value, TextField, URLField
from django.db.models.functions import Cast, Concat
from django.db.models.query import QuerySet
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch
from django.utils import timezone

from ssl_cert_tracker.models import Subscription
from ssl_cert_tracker.lib import Email

LOGGER = logging.getLogger('django')


def get_absolute_admin_change_url(
        admin_view, obj_pk, obj_anchor_name=None, root_url=None):
    """
    build and return an absolute `URL` for a `Django admin change` page

    See `Reversing admin URLs
    <https://docs.djangoproject.com/en/2.2/ref/contrib/admin/#reversing-admin-urls>`__.

    :arg str admin_view: the name of the admin view
    :arg int obj_pk: the primary key of the object in the view
    :arg str obj_anchor_name: the string that should be placed inside
        an <a>$obj_anchor_name</a> `HTML` tag; default is `None` and
        in that case the function assumes that the HTML tag will be
        <a></a>

    :arg str root_url: an `URL` fragment to be placed before the
        `Django admin` object path

        It is supposed to look something like
        '<a href="http://server:port/'. If this argument is set to `None`,
        it will be populated from specific `Django` settings and the
        value returned by :meth:`socket.getfqdn`

    """
    if root_url is None:
        root_url = (
            f'<a href="{settings.SERVER_PROTO}://{socket.getfqdn()}:'
            f'{settings.SERVER_PORT}/')

    if obj_anchor_name is None:
        tail_url = '"></a>'
    else:
        tail_url = f'">{obj_anchor_name}</a>'

    try:
        admin_path = reverse(admin_view, args=(obj_pk,))
    except NoReverseMatch as err:
        return f'cannot resolve URL path for view {admin_view}. Error: {err}'

    return f'{root_url}{admin_path}{tail_url}'


def diagnose_network_problem(host_spec, port=0):
    """
    diagnose problems with noetwork nodes

    This function looks for:

    * host names that are not in DNS

      if the `host_spec` is not an `IP` address, this function will use
      :meth:`socket.getaddrinfo` to simualte opening a socket to the
      host. meth:`socket.getaddrinfo` will fail if the host name is not in
      DNS

    * host ip addresses that do not exist on the network

      if the `host_spec` is an `IP` address, the function uses
      :meth:`socket.gethostbyaddr` to verify that the host is on the
      network

    :arg str host_spec: the host name or IP address

    :arg int port: the port argument to use with meth:`socket.getaddrinfo`,
        default is 0

    :returns: an explicit error message or a "can't find anything wrong"
        message
    :rtype: str
    """
    try:
        ipaddress.ip_address(host_spec)
        try:
            socket.gethostbyaddr(host_spec)
        except Exception as err:  # pylint: disable=broad-except
            return (f'\nhost {host_spec} does not exist,'
                    f' error {type(err)}: {str(err)}')

    except ValueError:
        try:
            socket.getaddrinfo(host_spec, port)
        except Exception as err:  # pylint: disable=broad-except
            return (f'host name {host_spec} not in DNS,'
                    f' error {type(err)}: {str(err)}')

    return f'found no network problems with host: {host_spec}'


class Timer():
    """
    `Context manager
    <https://docs.python.org/3/library/stdtypes.html#context-manager-types>`__
    class that provides timing functionality for evaluating the performance
    and/or response time of a `Python` `function
    <https://docs.python.org/3/library/stdtypes.html#functions>`__ or
    `method
    <https://docs.python.org/3/library/stdtypes.html#methods>`__
    """

    def __init__(
            self,
            description='method timing context manager', use_duration=True):
        """
        constructor for the :class:`Timer` class
        """
        self.description = description
        """
        provide a :class:`str` description for the context manager

        Default:'method timing context manager'
        """

        self.start = None
        """the start time"""

        self.end = None
        """the end time"""

        self.elapsed = None
        """
        the time elapsed while executing the method or function invoked
        with the :class:`Timer` context manager

        This is a :class:`float` value expressed in seconds
        """

        self.use_duration = use_duration
        """
        use seconds or :class:`datetime.timedelta` objects for the timer

        Default (`True`) is to use :class:`datetime.timedelta` objects
        """

    def __enter__(self):
        """
        start the timer and expose the instance attributes to the outside
        world

        `return self` ensures that the :attr:`elapsed` instance attribute
        (as well as all the other instance attributes) will be available
        once the context manager goes out of scope.
        """
        self.start = time.perf_counter()
        return self

    def __exit__(self, type, value, traceback):
        """
        stop the timer and update the :attr:`elapsed` instance attribute

        'return False` ensures that exceptions raised within the context
        manager scope will propagate to the outside world.
        """
        self.end = time.perf_counter()
        self.elapsed = self.end - self.start
        if self.use_duration:
            self.elapsed = datetime.timedelta(seconds=self.elapsed)

        return False


class UnknownDataTargetError(Exception):
    """
    custom :exc:`Exception` class raised when the :func:`get_model` function
    cannot find the requested data model
    """


class DataTargetFieldsAttributeError(Exception):
    """
    custom :exc:`Exception class raised when the
    :func:`get_queryset_values_keys` cannot find attribute :attr:`qs_fields`
    """


def get_uuid():
    """
    provide default values for UUID fields

    :returns: an instance of :class:`uuid.UUID` that can  be used as a
              unique identifier
    """
    return uuid.uuid4()


def get_model(destination):
    """
    get a :class:`django.db.models.Model` object

    This function takes a :class:`str` argument and returns the matching
    :class:`django.db.models.Model` model if possible. We use this function
    because :class:`django.db.models.Model` objects cannot be ``JSON``
    serialized when `calling Celery tasks
    <https://docs.celeryproject.org/en/latest/userguide/calling.html#serializers>`_.
    Using this function, the workaround is

    .. code-block:: python

        from p_soc_auto_base.utils import get_model

        @shared_task
        def a_task(model_name_as_string):
            my_django_model = get_model(model_name_as_string)

            return do_something_with(my_django_model)

    :arg str destination: the 'app_name.model_name' string for a `model`

    :returns: the matching :class:`django.db.models.Model` model object

    :raises:

        :exc:`UnknownDataTargetError` if there is no matching model
        registered on the server

    """
    try:
        return apps.get_model(*destination.split('.'))
    except Exception as err:
        raise UnknownDataTargetError from err


def get_queryset_values_keys(model):
    """
    A :class:`Django queryset <django.db.models.query.QuerySet>` can have
    data fields (straight database fields) and calculated fields (the
    result of calculations performed at the database level, e.g. `Count` or
    `Sum` aggregated fields).
    If the `queryset` does have calculated fields, the names of these fields
    will be present in the :attr:`django.db.models.Model.qs_fields` attribute
    of the `model` on which the `queryset` is based.

    This function returns the :attr:`django.db.models.Model.qs_fields`
    attribute if it exists

    :returns: the :attr:`django.db.models.Model.qs_fields` :class:`list`

    :Note:

        These field names are for the `queryset`, **not for the
        `model` that is the source of the `queryset`**.

    :raises: :exc:`DataTargetFieldsAttributeError` if the `qs_fields`
        attribute is not present
    """
    if not hasattr(model, 'qs_fields'):
        raise DataTargetFieldsAttributeError(
            'model %s is missing the qs_fields attribute'
            % model._meta.model_name)

    return model.qs_fields


def url_annotate(queryset):
    """
    annotate each row in a :class:`Django queryset
    <django.db.models.query.QuerySet>` with the absolute path of the `URL` for
    the related :class:`Django admin <django.contrib.admin.ModelAdmin>` instance

    See `Reversing admin URLs
    <https://docs.djangoproject.com/en/2.2/ref/contrib/admin/#reversing-admin-urls>`_.

    Note that this fail if the `Django Admin Site
    <https://docs.djangoproject.com/en/2.2/ref/contrib/admin/#module-django.contrib.admin>`_
    is not enabled.

    This function uses the `Model _meta API
    <https://docs.djangoproject.com/en/2.2/ref/models/meta/#module-django.db.models.options>`_
    to extract the `name` of the `primary key` field, the `app_label` property,
    and the `model_name` property.
    It then uses the `Concat
    <https://docs.djangoproject.com/en/2.2/ref/models/database-functions/#concat>`_
    database function to calculate a field containting the value of the `URL`.

    :arg queryset: the :class:`<django.db.models.query.QuerySet>` object

    :returns: the queryset with an additional field named url

    :raises:

        :exc:`TypeError` if the argument is not a
        :class:`Django queryset <django.db.models.query.QuerySet>`

    """
    if not isinstance(queryset, QuerySet):
        raise TypeError(
            'bad type %s for object %s' % (type(queryset), queryset))

    obj_sample = queryset.model._meta

    return queryset.annotate(url_id=Cast(obj_sample.pk.name, TextField())).\
        annotate(url=Concat(
            Value(settings.SERVER_PROTO), Value('://'),
            Value(socket.getfqdn()),
            Value(':'), Value(settings.SERVER_PORT),
            Value('/admin/'),
            Value(obj_sample.app_label), Value(
                '/'), Value(obj_sample.model_name),
            Value('/'), F('url_id'), Value('/change/'),
            output_field=URLField()))


def details_url_annotate(
        queryset, app_path=None,
        model_path=None, param_name=None, param_lookup_name=None):
    """
    annotate each row in a `queryset` with an admin link to related records

    For example, we have a hosts and host events and host events linked via a
    :class:`Django Foreign Key
    <django.db.models.ForeignKey>` field. This function will annotate each row in
    the hosts `queryset` with the absolute `Django admin URL` to the related
    host events like below::

        http://10.2.50.35:8080/admin/citrus_borg/winlogevent/?source_host__host_name=bccss-t450s-02

    :arg queryset: the initial :class:`Django queryset
        <django.db.models.query.QuerySet>`

    :arg str app_path: the `app_label` for the model with the details.
        If ``None``, the `app_label` is picked from the `queryset` using the
        `Model _meta API
        <https://docs.djangoproject.com/en/2.2/ref/models/meta/#module-django.db.models.options>`_.
        This is only useful if the master and the details models are defined in the
        same `Django application`.

    :arg str model_path: the `model_name` property of the `Django model` with the
        details. If ``None``, it will be picked from the `queryset` using the
        `Model _meta API`. This, however, is o very little use, since there are
        very few realistic data models where the master and the details are in
        the same `Djanog model`.

    :arg str param_name: `Django lookup` key_name__field_name used to build the
        `param` part of the `URL`. If one considers the example above, this
        argument is 'source_host__host_name' which means that the events
        (the details) model has a foreign key named 'source_host' pointing to
        the hosts (master) model and the lookup will be applied against a
        field named 'host_name' in the later model.

    :arg str param_lookup_name: the name of the field that contains the `value`
        part of the `URL`. If one considers the example above, the value used
        in the filter is picked from the field containing the host_name.
    """
    if not isinstance(queryset, QuerySet):
        raise TypeError(
            'bad type %s for object %s' % (type(queryset), queryset))

    if param_name is None:
        raise ValueError(
            'cannot build URL parameters without a parameter name')

    if param_lookup_name is None:
        raise ValueError(
            'cannot build URL parameters without a parameter value')

    obj_sample = queryset.model._meta

    if app_path is None:
        app_path = obj_sample.app_label

    if model_path is None:
        model_path = obj_sample.model_name

    try:
        return queryset.annotate(details_url=Concat(
            Value(settings.SERVER_PROTO), Value('://'),
            Value(socket.getfqdn()),
            Value(':'), Value(settings.SERVER_PORT),
            Value('/admin/'),
            Value(app_path), Value(
                '/'), Value(model_path),
            Value('/?'), Value(param_name), Value('='), F(param_lookup_name),
            output_field=URLField()))
    except Exception as error:
        raise error


def remove_duplicates(sequence=None):
    """
    remove duplicates from a sequence

    We are not using the `set(list)` approach because that one only works with
    :class:`list <list>`. this approach will also work with :class:`strings <str>`.

    :arg sequence: the sequence that may be containing duplicates

    :returns: a :class:`lst` with no duplicate items
    """
    class IterableError(Exception):
        """
        raise when the input is not, or cannot be cast to, an iterable
        """

        def __init__(self, sequence):
            message = (
                '%s of type %s is not, or cannot be cast to, a sequence' %
                (sequence, type(sequence)))

            super().__init__(message)

    if sequence is None:
        raise IterableError(sequence)

    if not isinstance(sequence, (str, list, tuple)):
        try:
            sequence = [sequence]
        except Exception:
            raise IterableError(sequence)

    no_dup_sequence = []
    _ = [no_dup_sequence.append(item)
         for item in sequence if item not in no_dup_sequence]

    return no_dup_sequence


def get_pk_list(queryset, pk_field_name='id'):
    """
    :returns: a :class:`lst` with the primary key values from a
        :class:`Django queryset <django.db.models.query.QuerySet>`

    needed when invoking `celery tasks` without forcing the use of the `pickle`
    serializer:

    * if we pass around `model` instances, we must use `pickle` and that is a
      security problem

    * the proper pattern is to pass around primary keys (usually :class:`int`)
      which are `JSON` serializable and pulling the `model` instance from the
      database inside the `celery task`. Note that this will increase the number
      of database access calls considerably

    :arg queryset: the `queryset`
    :type queryset: :class:`django.db.models.query.QuerySet`

    :arg str pk_field_name: the name of the primary key field; in `Django` primary
        keys are by default using the name 'id'.

    """
    return list(queryset.values_list(pk_field_name, flat=True))


def _make_aware(datetime_input, use_timezone=timezone.utc, is_dst=False):
    """
    make sure that a :class:`datetime.datetime` object is `timezone aware
    <https://docs.python.org/3/library/datetime.html#module-datetime>`_

    :arg `datetime.datetime` datetime_input:

    :arg `django.utils.timezone` use_timezone: the timezone to use

    :arg bool is_dst: use `Daylight saving time
        <https://en.wikipedia.org/wiki/Daylight_saving_time>`_

    """
    if timezone.is_aware(datetime_input):
        return datetime_input

    return timezone.make_aware(
        datetime_input, timezone=use_timezone, is_dst=is_dst)


class MomentOfTime():
    """
    Utility class for calculating a `datetime.datetime` moment
    relative to another `datetime.datetime` moment (the reference
    moment) when a `datetime.timedelta` interval is provided.

    In most cases the reference moment is the value returned by the
    :meth:`datetime.dateime.now` method but sometimes we need something else.

    Note that this class uses the `django.utils.timezone
    <https://docs.djangoproject.com/en/2.2/ref/utils/#module-django.utils.timezone>`__
    module instead of the `Python datetime
    <https://docs.python.org/3/library/datetime.html#module-datetime>`_ module.
    Therefore, it should not be used outside `Django applications`.

    .. todo::

        This class is time zone aware but only operates with UTC. Do we
        need to make it work with other time zones and, particularly,
        with the time zone defined in the Dajngo settings?

    """
    @staticmethod
    def now(now):
        """
        `static method
        <https://docs.python.org/3/library/functions.html?highlight=staticmethod#staticmethod>`__
        for calculating the reference moment

        :arg `datetime.datetime` now: the reference moment; if ``None``, use the
            value returned by :meth:`django.utils.timezone.now`

        :raises: :exc:`TypeError` if it cannot create or return a
            :class:`datetime.datetime` moment
        """
        if now is None:
            now = timezone.now()

        if not isinstance(now, timezone.datetime):
            raise TypeError(
                'Invalid object type %s, was expecting datetime' % type(now))

        return now

    @staticmethod
    def time_delta(time_delta, **kw_time_delta):
        """
        `static method
        <https://docs.python.org/3/library/functions.html?highlight=staticmethod#staticmethod>`_
        for verifying or calculating a :class:`django.utils.timezone.timedelta`
        object

        :returns: a proper :class:`datetime.timedelta` object. if the time_delta argument
            is not provided, use the :class:`kw_time_delta dictionary <dict>` to
            create a :class:`datetime.timedelta` object

        :arg `datetime.timedelta` time_delta: if this argument is provided, the
            static method will return it untouched

        :arg dict kw_time_delta: a :class:`dict` suitable for creating a
            :class:`datetime.timedelta` object. See
            `<https://docs.python.org/3/library/datetime.html?highlight=timedelta#datetime.timedelta>`__.

        :raises:

            :exc:`TypeError` when it cannot return a :class:`datetime.timedelta`

        """

        if time_delta is None:
            try:
                time_delta = timezone.timedelta(**kw_time_delta)
            except TypeError as error:
                raise error

        if not isinstance(time_delta, timezone.timedelta):
            raise TypeError(
                'Invalid object type %s, was expecting timedelta'
                % type(time_delta))

        return time_delta

    @classmethod
    def past(cls, **moment):
        """
        `class method
        <https://docs.python.org/3/library/functions.html?highlight=classmethod#classmethod>`_
        that returns a moment in the past relative to the reference moment

        :arg dict moment: `keyword arguments
            <https://docs.python.org/3/tutorial/controlflow.html#keyword-arguments>`_
            with the following keys:

            :now: contains the reference moment; if not present, this method
                  will use the value returned by :meth:`django.utils.timezone.now`.

            :time_delta: contains the `datetime.timedelta` interval used to
                calculate the moment in the past.

                If this key is not present, the method expects other keys
                as per
                `<https://docs.python.org/3/library/datetime.html?highlight=timedelta#datetime.timedelta>`__
                so that a `datetime.timedelta` interval can be calculated

        """
        return MomentOfTime.now(now=moment.pop('now', None)) \
            - MomentOfTime.time_delta(
                time_delta=moment.pop('time_delta', None), **moment)

    @classmethod
    def future(cls, **moment):
        """
        `class method
        <https://docs.python.org/3/library/functions.html?highlight=classmethod#classmethod>`_
        that returns a moment in the future relative to the reference moment

        See :meth:`past` for details.
        """
        return MomentOfTime.now(now=moment.pop('now', None)) \
            + MomentOfTime.time_delta(
                time_delta=moment.pop('time_delta', None), **moment)


def get_base_queryset(data_source, **base_filters):
    """
    :returns: a :class:`Django queryset <django.db.models.query.QuerySet>`
        associated with a :class:`Django model <django.db.models.Model>`

        If the filters optional arguments are provided, the `Django queryset`
        will be filtered accordingly

    :arg str data_source: a model name in the format 'app_label.model_name'
    :arg dict base_filters: optional arguments to be used for the `filter()
        <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#filter>`_
        method of the `queryset`

        For example:

        .. ipython::

            In [1]: from p_soc_auto_base.utils import get_base_queryset

            In [2]: qs = get_base_queryset('citrus_borg.borgsite')

            In [3]: qs.values('site', 'enabled')
            Out[3]: <QuerySet [{'site': 'Squamish', 'enabled': False}, {'site': 'LGH', 'enabled': False}, {'site': 'Whistler', 'enabled': False}, {'site': 'Pemberton', 'enabled': False}, {'site': 'Bella Bella', 'enabled': False}, {'site': 'Bella Coola', 'enabled': False}, {'site': 'Sechelt', 'enabled': False}, {'site': 'Powell River', 'enabled': False}, {'site': 'over the rainbow', 'enabled': True}, {'site': 'Bella Bella-wifi', 'enabled': False}, {'site': 'Bella Coola-wifi', 'enabled': False}, {'site': 'Whistler-wifi', 'enabled': False}, {'site': 'Pemberton-wifi', 'enabled': False}, {'site': 'LGH-wifi', 'enabled': False}, {'site': 'Squamish-wifi', 'enabled': False}]>

            In [4]: qs = get_base_queryset('citrus_borg.borgsite', enabled=True)

            In [5]: qs.values('site', 'enabled')
            Out[5]: <QuerySet [{'site': 'over the rainbow', 'enabled': True}]>

            In [6]:


    :raises:

        :exc:`LookupError` if the model cannot be found

            either the app_label is not present in the INSTALLED_APPS section
            in the settings, or the model doesn't exist in the app

        :exc:`django.core.exceptions.FieldError` if there are invalid filter
            specifications in the base_filters optional arguments
    """
    try:
        model = apps.get_model(data_source)
    except LookupError as error:
        raise error

    queryset = model.objects.all()

    if base_filters:
        try:
            queryset = queryset.filter(**base_filters)
        except FieldError as error:
            raise error

    return queryset


def get_subscription(subscription):
    """
    :returns: a :class:`ssl_cert_tracker.models.Subscription` instance

    :arg str subscription: the subscription value
        Note that this value is case-sensitive

    .. todo::

        Use `filter(subscription__iexact=subscription).get()` to avoid the case
        sensitive requirement

    :raises: :exc:`Exception` if the
        :class:`ssl_cert_tracker.models.Subscription` instance cannot be found

    .. todo::

        Change the error catching to use a
        :exc:`djang.db.core.exceptions.ObjectDoesNotExist` exception.
    """
    try:
        return Subscription.objects.\
            get(subscription=subscription)
    except Exception as error:
        raise error


def borgs_are_hailing(
        data, subscription, logger=LOGGER, add_csv=True, **extra_context):
    """
    use the :class:`ssl_cert_tracker.lib.Email` class to prepare and send an
    email from the :ref:`SOC Automation Server`

    :arg data: a :class:`Django queryset <django.db.models.query.QuerySet>`

    :arg str subscription: the key for retrieving the :class:`Subscription
        <ssl_cert_tracker.models.Subscription>` instance that will be used
        for rendering and addressing the email

        The :class:`Subscription <ssl_cert_tracker.models.Subscription>`
        instance must contain a descriptor for the `queryset` fields that
        will be rendered in the email.

        The :class:`Subscription <ssl_cert_tracker.models.Subscription>`
        instance must contain the name and location of the template that
        will be used to render the email.

    :arg bool add_csv: attach a csv file with the contents of the `data`
        argument to the email; default is `True`

    :arg LOGGER: a logging handlle
    :type LOGGER: :class:`logging.Logger`

    :arg dict extra_context: optional arguments with additional data to be rendered
        in the email

    :raises: :exc:`Exception` if the email cannot be rendered or if the email
        cannot be sent

        We are using generic :class:`exceptions <Exception>` because this function
        is almost always invoked from a `Celery task
        <https://docs.celeryproject.org/en/latest/userguide/tasks.html>`_ and
        `Celery` will do all the error handling work if needed.

        .. todo::

            We need a custom error for rendering the email and an SMTP related
            error for sending the email.
    """
    try:
        email_alert = Email(
            data=data, subscription_obj=subscription, logger=logger,
            add_csv=add_csv, **extra_context)
    except Exception as error:  # pylint: disable=broad-except
        logger.error('cannot initialize email object: %s', str(error))
        raise error

    try:
        return email_alert.send()
    except Exception as error:
        logger.error(str(error))
        raise error
