"""
.. _utils:

:module:    p_soc_auto.p_soc_auto_base.utils

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:update:    Jul. 15, 2019

This module contains utility `Python` classes and functions used by the
`Django` applications  of the :ref:`SOC Automation Server`.

"""
import logging
import socket

from django.apps import apps
from django.core.exceptions import FieldError
from django.conf import settings
from django.db.models import F, Value, TextField, URLField
from django.db.models.functions import Cast, Concat
from django.db.models.query import QuerySet
from django.utils import timezone

from ssl_cert_tracker.models import Subscription
from ssl_cert_tracker.lib import Email

LOGGER = logging.getLogger('django')


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
    <django.db.models.query.QuerySet>` with the absolute path of the admin url
    of the underlying :class:`Django model <django.db.models.Model>` instance

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

    :arg `datetime.datetime datetime_input:

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
    <https://docs.djangoproject.com/en/2.2/ref/utils/#module-django.utils.timezone>`_
    module instead of the `Python datetime
    <https://docs.python.org/3/library/datetime.html#module-datetime>`_ module.
    Therefore, it should not be used outside `Django applications`.
    """
    @staticmethod
    def now(now):
        """
        `static method
        <https://docs.python.org/3/library/functions.html?highlight=staticmethod#staticmethod>`_
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
            `<https://docs.python.org/3/library/datetime.html?highlight=timedelta#datetime.timedelta>`_.

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
                         `<https://docs.python.org/3/library/datetime.html?highlight=timedelta#datetime.timedelta>`_
                         so that a `datetime.timedelta` interval can be calculated.

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
    return a queryset associated with a given django model.
    if the filters optional arguments are provide the queryset
    will be filtered accordingly

    :arg str data_source: a model name in the format 'app_label.model_name'
    :returns: the queryset associated with the data source

    :arg **base_filters: django filters to be applied to the queryset

        example: if something like enabled=True is part of :arg:**base_filters,
        the queryset returned will have .filter(enabled=True) applied

    :raises:

        :exception:`<exceptions.LookupError>` if the model cannot be found.
        either the app_label is not present in the INSTALLED_APPS section
        in the settings, or the model doesn't exist in the app

    :raises:

        :exception:`<django.core.exceptions.FieldError>` if there are invalid
        filter specifications in the base_filters optional arguments
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
    :returns: a :class:`<ssl_cert_tracker.models.Subscription>` instance
    """
    try:
        return Subscription.objects.\
            get(subscription=subscription)
    except Exception as error:
        raise error


def borgs_are_hailing(data, subscription, logger=LOGGER, **extra_context):
    """
    prepare and send emails from the citrus_borg application
    """
    try:
        email_alert = Email(
            data=data, subscription_obj=subscription, logger=logger,
            **extra_context)
    except Exception as error:  # pylint: disable=broad-except
        logger.error('cannot initialize email object: %s', str(error))
        raise error

    try:
        return email_alert.send()
    except Exception as error:
        logger.error(str(error))
        raise error
