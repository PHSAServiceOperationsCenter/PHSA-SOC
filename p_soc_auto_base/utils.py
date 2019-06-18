"""
.. _utils:

utility classes and functions for the p_soc_auto project

:module:    p_soc_auto.p_soc_auto_base.utils

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:update:    Feb. 1, 2019

"""
import logging

from django.apps import apps
from django.core.exceptions import FieldError
from django.utils import timezone

from ssl_cert_tracker.models import Subscription
from ssl_cert_tracker.lib import Email

LOGGER = logging.getLogger('django')


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
        return 'cannot initialize email object: %s' % str(error)

    try:
        return email_alert.send()
    except Exception as error:
        logger.error(str(error))
        raise error
