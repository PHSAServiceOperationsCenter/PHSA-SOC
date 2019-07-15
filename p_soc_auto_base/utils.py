"""
.. _utils:

utility classes and functions for the p_soc_auto project

:module:    p_soc_auto.p_soc_auto_base.utils

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:update:    Jul. 15, 2019

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
    raise when trying to upload to an unknown data model
    """


class DataTargetFieldsAttributeError(Exception):
    """
    raise when the target model doesn't have a qs_fields attribute
    """


def get_model(destination):
    """
    get the model where the data is to be saved
    """
    try:
        return apps.get_model(*destination.split('.'))
    except Exception as err:
        raise UnknownDataTargetError from err


def get_queryset_values_keys(model):
    """
    this function returns a list of keys that will be passed to
    :method:`<django.db.models.query.QuerySet.values>`

    :returns: a `list of field names

        note that these field names are for the queryset, **not for the
        model that is the source of thew queryset**, because a queryset
        can contain fields defined via annotations and/or aggregations

    :raises: :exception:`<DataTargetFieldsAttributeError>`
    """
    if not hasattr(model, 'qs_fields'):
        raise DataTargetFieldsAttributeError(
            'model %s is missing the qs_fields attribute'
            % model._meta.model_name)

    return model.qs_fields


def url_annotate(queryset):
    """
    annotate a queryset with the admin url of the underlying model

    :arg queryset: the :class:`<django.db.models.query.QuerySet>` object

    :returns: the queryset with an additional field named url

    :raises:

        :exception:`<TypeError>` if the argument is nnot a queryset
    """
    if not isinstance(queryset, QuerySet):
        raise TypeError(
            'bad type %s for object %s' % (type(queryset), queryset))

    # get the object metadata from an (the first) element of the queryset
    # we need the app_label, model_name, and primary key field name so
    # that we can build the url value
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
    annotate a queryset with an admin link to related records
    http://10.2.50.35:8080/admin/citrus_borg/winlogevent/?source_host__host_name=bccss-t450s-02
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

    :arg sequence: the sequence that may be containing duplicates

    :returns: a ``list`` with no duplicate items
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

    if not isinstance(sequence, (list, tuple)):
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
    get the primary key values from a queryset

    needed when invoking celery tasks without a pickle serializer:

        *    if we pass around model instances, we must use pickle and that
             is a security problem

        *    the proper pattern is to pass around primary keys (usually
             ``int``) which are JSON serializable and pulling the instance
             from the database inside the celery task. note that this will
             increase the number of database access calls considerably

    :arg queryset: the (pre-processed) queryset
    :type queryset: :class"`<django.db.models.query.QuerySet>`

    :arg str pk_field_name:

        the name of the primary key field, (``django``) default 'id'

    :returns: a ``list`` of primary key values
    """
    return list(queryset.values_list(pk_field_name, flat=True))


def _make_aware(datetime_input, use_timezone=timezone.utc, is_dst=False):
    """
    make datetime objects to timezone aware if needed
    """
    if timezone.is_aware(datetime_input):
        return datetime_input

    return timezone.make_aware(
        datetime_input, timezone=use_timezone, is_dst=is_dst)


class MomentOfTime():
    """
    quick and dirty way of calculating a ``datetime.datetime`` object
    relative to another ``datetime.datetime`` object (the reference
    moment) when a ``dateime.timedelta`` is provided.

    in most cases the reference moment is the value returned by
    :method:`<datetime.dateime.now>` but sometimes we need something else
    """
    @staticmethod
    def now(now):
        """
        static method for the now reference moment
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
        return a proper ``datetime.timedelta`` object. if a dictionary is
        provided instead, try to build the object from the dictionary

        :raises:

            ``exceptions.TypeError`` when :arg:`<time_delta>`` is not of the
            proper type or if the input dictionary cannot be used as argument
            for ``datetime.timedelta``

        :param time_delta: default ``None``
        :type time_delta: ``datetime.timedelta``
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
        moment in the past
        """
        return MomentOfTime.now(now=moment.pop('now', None)) \
            - MomentOfTime.time_delta(
                time_delta=moment.pop('time_delta', None), **moment)

    @classmethod
    def future(cls, **moment):
        """
        future moment
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
