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
from django.utils import timezone


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
