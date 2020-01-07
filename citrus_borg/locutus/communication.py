"""
.. _communication:

Communication Module
--------------------

:module:    citrus_borg.locutus.communication

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

:updated:    Jun. 19, 2019

This module contains database functions for the :ref:`Citrus Borg Application`.

"""
import datetime

from enum import Enum

from django.db.models import (
    Count, Q, Min, Max, Avg, StdDev, DurationField, Value,
    BigIntegerField, CharField,
)
from django.db.models.functions import TruncHour, TruncMinute
from django.utils import timezone

from citrus_borg.models import (
    WinlogEvent, WinlogbeatHost, KnownBrokeringDevice, BorgSite,
)
from citrus_borg.dynamic_preferences_registry import get_preference


class GroupBy(Enum):
    """
    Enumeration class for specifying the `group by` time sequence details
    """
    NONE = None
    HOUR = 'hour'
    MINUTE = 'minute'


def get_dead_bots(now=None, time_delta=None):
    """
    get the bot hosts that have not sent any `ControlUp` events during
    the interval defined by the arguments

    "Interval defined by the arguments" is a hoity toity way of saying
    "over the last $x seconds/minutes/hours (etc)".

    The idea behind this function is to return the difference between a
    list of all the bot hosts and a list of the bot hosts that have been heard
    from during the defined interval.
    The result will be the list of bots that have **not** been heard from
    during the defined interval.

    This function is an excellent candidate for using the `difference()
    <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#difference>`__
    method of the :class:`django.db.models.query.QuerySet` but, unfortunately,
    that method doesn't work with `MariaDB` databases.

    The workaround is to cast the diffing :class:`QuerySets
    <django.db.models.query.QuerySet>` to :class:`lists <list>` using the
    `values_list()
    <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#values-list>`__
    method.
    Diff the :class:`lists <list>` using the `symmetric_difference()
    <https://docs.python.org/3.6/library/stdtypes.html#frozenset.symmetric_difference>`__
    method of the `Python set class
    <https://docs.python.org/3.6/library/stdtypes.html#set-types-set-frozenset>`__,
    and then cast the result to a :class:`django.db.models.query.QuerySet`.

    The list of live bots is extracted from the
    :class:`citrus_borg.models.WinlogEvent`

    :arg datetime.datetime now: the initial moment

        By default (and in most useful cases for functions that return
        historical data), the initial moment should be the value of
        :meth:`datetime.datetime.now`. In `Django` applications, it is
        recommended to use :meth:`django.utils.timezone.now` which is
        what all the functions in this module do

    :arg datetime.timedelta time_delta: the time interval to consider

        By default, this will be retrieved from the dynamic preference
        `Bot not seen alert threshold
        <../../../admin/dynamic_preferences/globalpreferencemodel/?q=dead_bot_after>`__

    :returns: a :class:`django.db.models.query.QuerySet` based on the
        :class:`citrus_borg.models.WinlogbeatHost` model

        The :class:`django.db.models.query.QuerySet` is `annotated
        <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
        with the arguments defining the interval.

    :raises: :exc:`TypeError` if the function arguments are not of the expected
        types

    """
    if now is None:
        now = timezone.now()

    if time_delta is None:
        time_delta = get_preference('citrusborgnode__dead_bot_after')

    if not isinstance(now, datetime.datetime):
        raise TypeError('%s type invalid for %s' % (type(now), now))

    if not isinstance(time_delta, datetime.timedelta):
        raise TypeError(
            '%s type invalid for %s' % (type(time_delta), time_delta))

    live_bots = list(WinlogEvent.objects.
                     filter(created_on__gt=now - time_delta).distinct().
                     values_list('source_host__host_name', flat=True))

    all_bots = list(WinlogbeatHost.objects.filter(enabled=True).
                    values_list('host_name', flat=True))

    dead_bots = set(all_bots).symmetric_difference(set(live_bots))

    dead_bots = WinlogbeatHost.objects.filter(host_name__in=list(dead_bots),
                                              last_seen__isnull=False)

    dead_bots = dead_bots.\
        annotate(measured_now=Value(now, output_field=CharField())).\
        annotate(measured_over=Value(time_delta, output_field=DurationField()))

    if dead_bots.exists():
        dead_bots = dead_bots.order_by('last_seen')

    return dead_bots


def get_dead_brokers(now=None, time_delta=None):
    """
    get the `Citrix` session hosts that have not serviced any requests during
    the interval defined by the arguments

    This function is very similar to :func:`get_dead_bots`.
    The only differences are:

    * The data is pulled from the
      :class:`citrus_borg.models.KnownnBrokeringDevice`

    * The default value for the `time_delta` argument is picked from the
      dynamic preference `Session host not seen alert threshold
      <../../../admin/dynamic_preferences/globalpreferencemodel/?q=dead_session_host_after>`__
    """
    if now is None:
        now = timezone.now()

    if time_delta is None:
        time_delta = get_preference('citrusborgnode__dead_session_host_after')

    if not isinstance(now, datetime.datetime):
        raise TypeError('%s type invalid for %s' % (type(now), now))

    if not isinstance(time_delta, datetime.timedelta):
        raise TypeError(
            '%s type invalid for %s' % (type(time_delta), time_delta))

    live_brokers = list(WinlogEvent.objects.
                        filter(created_on__gt=now - time_delta,
                               event_state__iexact='successful').distinct().
                        values_list('xml_broker__broker_name', flat=True))

    all_brokers = list(KnownBrokeringDevice.objects.filter(enabled=True).
                       values_list('broker_name', flat=True))

    dead_brokers = set(all_brokers).symmetric_difference(set(live_brokers))

    dead_brokers = KnownBrokeringDevice.objects.\
        filter(broker_name__in=list(dead_brokers))
    if dead_brokers.exists():
        dead_brokers = dead_brokers.order_by('last_seen')

    return dead_brokers


def get_dead_sites(now=None, time_delta=None):
    """
    get the remote sites from where no `ControlUp` events have been delivered
    during the interval defined by the arguments.

    This function is very similar to :func:`get_dead_bots`.
    The only differences are:

    * The data is pulled from the
      :class:`citrus_borg.models.BorgSite`

    * The default value for the `time_delta` argument is picked from the
      dynamic preference `Site not seen alert threshold
      <../../../admin/dynamic_preferences/globalpreferencemodel/?q=dead_site_after>`__

    """
    if now is None:
        now = timezone.now()

    if time_delta is None:
        time_delta = get_preference('citrusborgnode__dead_site_after')

    if not isinstance(now, datetime.datetime):
        raise TypeError('%s type invalid for %s' % (type(now), now))

    if not isinstance(time_delta, datetime.timedelta):
        raise TypeError(
            '%s type invalid for %s' % (type(time_delta), time_delta))

    live_sites = list(WinlogEvent.objects.
                      filter(created_on__gt=now - time_delta).distinct().
                      values_list('source_host__site__site', flat=True))

    all_sites = list(BorgSite.objects.filter(enabled=True).
                     values_list('site', flat=True))

    dead_sites = set(all_sites).symmetric_difference(set(live_sites))

    dead_sites = BorgSite.objects.filter(site__in=list(dead_sites)).distinct()
    if dead_sites.exists():
        dead_sites = dead_sites.order_by('winlogbeathost__last_seen')

    return dead_sites


def get_logins_by_event_state_borg_hour(now=None, time_delta=None):
    """
    get the number of failed events and successful events during the interval
    defined by the arguments for each monitoring site aggregated by hour

    :arg datetime.datetime now: the initial moment
        By default the initial moment is the value returned by
        :meth:`django.utils.timezone.now`

    :arg datetime.timedelta time_delta: the time interval to consider
        By default, this will be retrieved from the dynamic preference
        `Dead if not seen for more than
        <../../../admin/dynamic_preferences/globalpreferencemodel/?q=dead_after>`__

    :returns: a :class:`django.db.models.query.QuerySet` based on the
        :class:`citrus_borg.models.WinlogbeatHost` model


    """
    if now is None:
        now = timezone.now()

    if time_delta is None:
        time_delta = get_preference('citrusborgcommon__dead_after')

    if not isinstance(now, datetime.datetime):
        raise TypeError('%s type invalid for %s' % (type(now), now))

    if not isinstance(time_delta, datetime.timedelta):
        raise TypeError(
            '%s type invalid for %s' % (type(time_delta), time_delta))

    return WinlogbeatHost.objects.\
        filter(winlogevent__created_on__gt=now - time_delta).\
        annotate(hour=TruncHour('winlogevent__created_on')).values('hour').\
        annotate(
            failed_events=Count(
                'winlogevent__event_state',
                filter=Q(winlogevent__event_state__iexact='failed'))).\
        annotate(
            successful_events=Count(
                'winlogevent__event_state',
                filter=Q(winlogevent__event_state__iexact='successful'))).\
        order_by('-hour', 'site__site')

# pylint: disable=too-many-arguments


def raise_ux_alarm(
        now=None, site=None, host_name=None,
        group_by=GroupBy.MINUTE, include_event_counts=False,
        time_delta=get_preference('citrusborgux__ux_alert_interval'),
        ux_alert_threshold=get_preference('citrusborgux__ux_alert_threshold')):
    """
    The `Windows` log events generated by the `ControlUp` client provide
    timing values for multiple `Citrix` events.
    Such timing values can be used for evaluating the performance of the
    `Citrix` application(s).

    This function will return the `ControlUp` hosts, sorted by site, where
    `ControlUp` events with timings worse than the value of the
    `ux_alert_threshold` argument averaged over the interval defined by the
    arguments `now` and `time_delta` have occurred.
    The timings considered when executing this function are:

    * The `Citrix` logon time

    * The store front connection time

    The data returned by the function is grouped by minute.

    :arg datetime.datetime now: the initial moment

        By default the initial moment is the value returned by
        :meth:`django.utils.timezone.now`

    :arg datetime.timedelta time_delta: the time interval to consider

        By default, this will be retrieved from the dynamic preference
        `Alert monitoring interval for citrix events
        <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ux_alert_interval>`__

    :arg str site: filter the :class:`django.db.models.query.QuerySet` by
        `site` using the value of this argument if not `None`

    :arg str host_name: filter the :class:`django.db.models.query.QuerySet` by
        `host_name` using the value of this argument if not `None`

    :arg group_by: how do you want to group the data in the
        :class:`django.db.models.query.QuerySet`?
    :type group_by: :class:`GroupBy`

    :arg datetime.timedelta ux_alert_threshold: the threshold for triggering
        this alert

        By default, this will be retrieved from the dynamic preference
        `Maximum acceptable response time for citrix events
        <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ux_alert_threshold>`__


    :returns: a :class:`django.db.models.query.QuerySet` based on the
        :class:`citrus_borg.models.WinlogbeatHost` model

        The :class:`django.db.models.query.QuerySet`  is `annotated
        <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
        with the value of the `ux_alert_threshold` argument

    :Note:

        In the :ref:`Citrus Borg Application`, the terms `Citrix performance`,
        `user experience`, and `Citrix response time` are considered more or
        less interchangeable.

    :Note:

        This function is using a relatively complex chain of function calls
        and can be considered an example of why `Django` query functions
        should be very specific even at the expense of code duplication.
        For example, this function returns a `Django` `queryset` but is
        impossible to determine the underlying `Django` `model` by looking
        at the source code of the function.
    """
    try:
        queryset = _by_site_host_hour(
            now=now, time_delta=time_delta, site=site, host_name=host_name,
            group_by=group_by, ux_alert_threshold=ux_alert_threshold,
            include_event_counts=include_event_counts)
    except Exception as error:
        raise error

    queryset = queryset.\
        annotate(
            ux_threshold=Value(ux_alert_threshold,
                               output_field=DurationField())).\
        order_by('site__site', 'host_name')

    if group_by == GroupBy.MINUTE:
        queryset = queryset.order_by('-minute')

    if group_by == GroupBy.HOUR:
        queryset = queryset.order_by('-hour')

    queryset = queryset.order_by(
        '-avg_logon_time', '-avg_storefront_connection_time')

    return queryset.order_by(
        'site__site', 'host_name', '-avg_logon_time',
        '-avg_storefront_connection_time')
# pylint: enable=too-many-arguments


def _include_event_counts(queryset):
    """
    `annotate
    <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
    a :class:`django.db.models.query.QuerySet` based on the
    :class:`citrus_borg.models.WinlogbeatHost` model with the counts for event
    states (states are `failed` and `successful`)

    :arg queryset: the :class:`django.db.models.query.QuerySet`

    :returns: a :class:`django.db.models.query.QuerySet`

    :Note:

        This function looks like a very abstract function but cannot be used
        anywhere but within this module and this application.
        This is specific to many `Django` based functions because of the
        conventional nature of `Django` programming. For example, one
        can access properties across models (classes) by using the
        `local_property__remote_property` convention.
        In this particular function, see `winlogevent__event_state__iexact`
        in the source code, which is an even more egregious example of a
        convention that will only work in `Django`:

        * `winlogevent` is not even defined by the programmer in the
          :class:`citrus_borg.models.WinlogbeatHost` code. `Django` will
          add it transparently as a reverse relationship to the
          :class:`citrus_borg.models.WinlogEvent` class

        * `__event_state` means that we only care about
          :attr:`citrus_borg.models.WinlogEvent.event_state`. Again this
          only works in `Django`

        * `__iexact` means that we are actually requesting a lookup against
          the field on the left hand side of the '__' token using a case
          insensitive exact match. This also only works in `Django` although
          there are other `Python` packages out there that have implemented
          this convention. E.g. the `Exchange Web Services client library
          <https://github.com/ecederstrand/exchangelib>`__ `Python` module
          implements this convention for searching within `Exchange` inbox
          data stores.

    """
    return queryset.\
        annotate(
            failed_events=Count(
                'winlogevent__event_state',
                filter=Q(winlogevent__event_state__iexact='failed'))).\
        annotate(
            undetermined_events=Count(
                'winlogevent__event_state',
                filter=Q(winlogevent__event_state__iexact='undetermined'))).\
        annotate(
            successful_events=Count(
                'winlogevent__event_state',
                filter=Q(winlogevent__event_state__iexact='successful')))


def _include_ux_stats(queryset):
    """
    `annotate
    <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
    a :class:`django.db.models.query.QuerySet` based on the
    :class:`citrus_borg.models.WinlogbeatHost` model with statistical values
    for `Citrix` application response times extracted from the
    :class:`citrus_borg.models.WinlogEvent` model

    The statistical functions used are: :class:`django.db.models.Avg`,
    :class:`django.db.models.Min`, :class:`django.db.models.Max` and
    :class:`django.db.models.StdDev`.

    The data items aggregated by this function are:

    * The store front connection duration

    * The receiver startup duration

    * The connection achieved duration

    * The logon achieved duration

    :arg queryset: the :class:`django.db.models.query.QuerySet`

    :returns: a :class:`django.db.models.query.QuerySet`

    """
    return queryset.annotate(
        min_storefront_connection_time=Min(
            'winlogevent__storefront_connection_duration')).\
        annotate(
            avg_storefront_connection_time=Avg(
                'winlogevent__storefront_connection_duration',
                output_field=DurationField())).\
        annotate(
            max_storefront_connection_time=Max(
                'winlogevent__storefront_connection_duration')).\
        annotate(
            stddev_storefront_connection_time=StdDev(
                'winlogevent__storefront_connection_duration')).\
        annotate(
            min_receiver_startup_time=Min(
                'winlogevent__receiver_startup_duration')).\
        annotate(
            avg_receiver_startup_time=Avg(
                'winlogevent__receiver_startup_duration',
                output_field=DurationField())).\
        annotate(
            max_receiver_startup_time=Max(
                'winlogevent__receiver_startup_duration')).\
        annotate(
            stddev_receiver_startup_time=StdDev(
                'winlogevent__receiver_startup_duration')).\
        annotate(
            min_connection_achieved_time=Min(
                'winlogevent__connection_achieved_duration')).\
        annotate(
            avg_connection_achieved_time=Avg(
                'winlogevent__connection_achieved_duration',
                output_field=DurationField())).\
        annotate(
            max_connection_achieved_time=Max(
                'winlogevent__connection_achieved_duration')).\
        annotate(
            stddev_connection_achieved_time=StdDev(
                'winlogevent__connection_achieved_duration')).\
        annotate(
            min_logon_time=Min('winlogevent__logon_achieved_duration')).\
        annotate(
            avg_logon_time=Avg(
                'winlogevent__logon_achieved_duration',
                output_field=DurationField())).\
        annotate(
            max_logon_time=Max('winlogevent__logon_achieved_duration')).\
        annotate(
            stddev_logon_time=StdDev('winlogevent__logon_achieved_duration'))

# pylint: disable=too-many-arguments,too-many-branches


def _by_site_host_hour(now, time_delta, site=None, host_name=None,
                       logon_alert_threshold=None, ux_alert_threshold=None,
                       include_event_counts=True, include_ux_stats=True,
                       group_by=GroupBy.HOUR):
    """
    create a complex :class:`django.db.models.query.QuerySet` based on the
    :class:`citrus_borg.models.WinlogbeatHost` model that is `annotated
    <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
    with statistical `aggregations
    <https://docs.djangoproject.com/en/2.2/topics/db/aggregation/#aggregation>`__
    extracted from the :class:`citrus_borg.models.WinlogEvent` model

    :arg datetime.datetime now: the initial moment

        By default the initial moment is the value returned by
        :meth:`django.utils.timezone.now`

    :arg datetime.timedelta time_delta: the time interval to consider

        By default, this will be retrieved from the dynamic preference
        `Ignore events created older than
        <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ignore_events_older_than>`__
        but it most cases this argument needs to be specified when invoking
        this function

    :arg str site: if present, filter the data that will be returned by `site`,
        otherwise return data for all known sites



    :arg str host_name: if present, filter the data that will be returned by
        'host_name`, otherwise return data for all known hosts

        Be careful when using the `site` and `host_name` arguments together.
        It is possible to come up with a combination of values for which
        no data can be returned (one filters by a host that lives at a site
        that was filtered out already). This function considers such a
        combination valid and will happily return an empty
        :class:`django.db.models.query.QuerySet` when invoked with such a
        combination.

    :arg int logon_alert_trehsold: if present, filter the data to be returned
        on the :class:`django.dn.models.Count` aggregation for `failed` events;
        only return records where the `failed` `Count` is greater than the
        value of this argument

    :arg `datetime.timedelta` ux_alert_threshold: if present, filter the data
        to by the :class:`django.dn.models.Avg` aggregation for event timings;
        only return rows where the average store front connection or the
        average logon duration are greater than or equal to the value of this
        argument

    :arg bool include_event_counts: `annotate` with `Count` for event states
        (successful and failed); default is `True`

    :arg bool include_ux_stats: `annotate` with the timing stats for
        `ControlUp` events; default is `True`

    :arg :class:`GroupBy` group_by: group the data to be returned by a time
        sequence; default is :attr:`GroupBy.HOUR`

        Note this will affect `aggregations
        <https://docs.djangoproject.com/en/2.2/topics/db/aggregation/#aggregation>`__.
        Normally, `aggregations` are calculated for the interval defined by the
        `now` and `time_delta` arguments but when this argument is present,
        the `aggregations` will be calculated for the time sequence value
        of the argument.

        The resulting `queryset` will look something like this:

        ==== ================== =========== ============= ======================
        site host               count fails count success hour
        ==== ================== =========== ============= ======================
        LGH  lgh01.healthbc.org 0           14            Aug. 1, 2019, midnight
        LGH  lgh01.healthbc.org 0           14            Aug. 1, 2019, 1 a.m.
        ==== ================== =========== ============= ======================

    :returns: a :class:`django.db.models.query.QuerySet`

    :raises:

        :exc:`TypeError` if the `now`, `time_delta`, and `ux_alert_threshold`
            are not of the expected type

        :exc:`ValueError` if the `logon_alert_threshold` argument is not
            an :class:`int`

    """
    if now is None:
        now = timezone.now()

    if time_delta is None:
        time_delta = get_preference(
            'citrusborgevents__ignore_events_older_than')

    if logon_alert_threshold is not None:
        try:
            logon_alert_threshold = int(logon_alert_threshold)
        except ValueError as error:
            raise error

    if ux_alert_threshold is not None:
        if not isinstance(ux_alert_threshold, datetime.timedelta):
            raise TypeError(
                '%s type invalid for %s' % (type(ux_alert_threshold),
                                            ux_alert_threshold))

    if not isinstance(now, datetime.datetime):
        raise TypeError('%s type invalid for %s' % (type(now), now))

    if not isinstance(time_delta, datetime.timedelta):
        raise TypeError(
            '%s type invalid for %s' % (type(time_delta), time_delta))

    queryset = WinlogbeatHost.objects.\
        filter(winlogevent__created_on__gt=now - time_delta)

    if site:
        queryset = queryset.filter(site__site__iexact=site)
        queryset = queryset.values('site__site')

    if host_name:
        queryset = queryset.filter(host_name__iexact=host_name)
        queryset = queryset.values('host_name')
    queryset = _group_by(queryset, group_by=group_by)

    if include_event_counts:
        queryset = _include_event_counts(queryset)

    if include_ux_stats:
        queryset = _include_ux_stats(queryset)

    if logon_alert_threshold:
        queryset = queryset.filter(
            Q(failed_events__gte=logon_alert_threshold) |
            Q(undetermined_events__gte=logon_alert_threshold))

    if ux_alert_threshold:
        queryset = queryset.\
            filter(
                Q(avg_storefront_connection_time__gte=ux_alert_threshold) |
                Q(avg_logon_time__gte=ux_alert_threshold) |
                Q(avg_receiver_startup_time__gte=ux_alert_threshold) |
                Q(avg_connection_achieved_time__gte=ux_alert_threshold) |
                Q(avg_receiver_startup_time__gte=ux_alert_threshold))

    queryset = queryset.\
        annotate(measured_now=Value(now, output_field=CharField())).\
        annotate(measured_over=Value(time_delta, output_field=DurationField()))

    return queryset
# pylint: enable=too-many-arguments,too-many-branches


def _group_by(queryset,
              group_field='winlogevent__created_on', group_by=GroupBy.NONE):
    """
    group the rows in a :class:`django.db.models.query.QuerySet` by a time
    sequence and `annotate` it with the time value

    See `Trunc
    <https://docs.djangoproject.com/en/2.2/ref/models/database-functions/#trunc>`__
    and `TimeField truncation
    <https://docs.djangoproject.com/en/2.2/ref/models/database-functions/#timefield-truncation>`__
    in the `Django` docs.

    The resulting `queryset` will look something like this:

    ==== ================== =========== ============= ======================
    site host               count fails count success hour
    ==== ================== =========== ============= ======================
    LGH  lgh01.healthbc.org 0           14            Aug. 1, 2019, midnight
    LGH  lgh01.healthbc.org 0           14            Aug. 1, 2019, 1 a.m.
    ==== ================== =========== ============= ======================


    :arg queryset: the :class:`django.db.models.query.QuerySet`

    :arg str group_field: the name of the :class:`django.db.models.Model`
        field that contains time data; this field must be a
        :class:`django.db.models.DateTimeField` or a
        :class:`django.db.models.TimeField` field

        Default is 'winlogevent__created_on'.

    :arg group_by: group the data to be returned by a time
        sequence; default is :attr:`GroupBy.HOUR`
    :type group_by: :class:`GroupBy`

    :returns: a :class:`django.db.models.query.QuerySet`

    """
    if group_by == GroupBy.HOUR:
        return queryset.\
            annotate(hour=TruncHour(group_field)).values('hour')

    if group_by == GroupBy.MINUTE:
        return queryset.\
            annotate(minute=TruncMinute(group_field)).values('minute')

    return queryset


def login_states_by_site_host_hour(
        now=None, time_delta=get_preference(
            'citrusborgevents__ignore_events_older_than'), site=None,
        host_name=None):
    """
    :returns: a :class:`django.db.models.query.QuerySet` based on the
        :class:`citru_borg.models.WinlogbeatHost` `annotated
        <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
        with all the `aggregations
        <https://docs.djangoproject.com/en/2.2/topics/db/aggregation/#aggregation>`__
        extracted from the :class:`citrus_borg.models.WinlogEvent` model
        calculated on a per hour basis for the interval defined by the
        `now` and `time_delta` arguments

    :arg datetime.datetime now: the initial moment

        By default the initial moment is the value returned by
        :meth:`django.utils.timezone.now`

    :arg datetime.timedelta time_delta: the time interval to consider

        By default, this will be retrieved from the dynamic preference
        `Ignore events created older than
        <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ignore_events_older_than>`__

    :arg str site: if present, filter the data that will be returned by `site`,
        otherwise return data for all known sites



    :arg str host_name: if present, filter the data that will be returned by
        'host_name`, otherwise return data for all known hosts

        Be careful when using the `site` and `host_name` arguments together.
        It is possible to come up with a combination of values for which
        no data can be returned (one filters by a host that lives at a site
        that was filtered out already). This function considers such a
        combination valid and will happily return an empty
        :class:`django.db.models.query.QuerySet` when invoked with such a
        combination

    :raises: :exc:`Exception` when failing

    """
    try:
        queryset = _by_site_host_hour(now, time_delta, site, host_name)
    except Exception as error:
        raise error

    return queryset.order_by('site__site', 'host_name', '-hour')


def raise_failed_logins_alarm(
        now=None, time_delta=None, failed_threshold=None):
    """
    :returns: alert data for failed logins

        The subject of such an alert is the monitoring bot. The alert is
        calculated based on the number of failed `ControlUp` failed logon events
        over a fixed interval.

        E.G. if a bot reports 2 or more failed logon events over a period of
        10 minutes, an alert will be raised.

        The alert information is returned via a
        :class:`django.db.models.query.QuerySet` based on the
        :class:`citrus_borg.models.WinlogbeatHost` model and `annotated
        <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
        with the data for the failed events extracted from the
        :class:`citrus_borg.models.WinlogEvent` model, and with the alert
        evaluation parameters (threshold and period)

    :arg datetime.datetime now: the initial moment

        By default the initial moment is the value returned by
        :meth:`django.utils.timezone.now`

    :arg datetime.timedelta time_delta: the time interval to consider

        By default, this will be retrieved from the dynamic preference
        `Logon alert after
        <../../../admin/dynamic_preferences/globalpreferencemodel/?q=logon_alert_after>`__

    :arg int failed_threshold: the number of failed logons that will trigger the
        alert

        By default, this will be retrieved from the dynamic preference
        `Failed logon events count alert threshold
        <../../../admin/dynamic_preferences/globalpreferencemodel/?q=logon_alert_threshold>`__

    :raises: :exc:`TypeError` if any of the function arguments do not satisfy type
        requirements

    """
    if now is None:
        now = timezone.now()

    if time_delta is None:
        time_delta = get_preference('citrusborglogon__logon_alert_after')

    if failed_threshold is None:
        failed_threshold = get_preference(
            'citrusborglogon__logon_alert_threshold')

    if not isinstance(now, datetime.datetime):
        raise TypeError('%s type invalid for %s' % (type(now), now))

    if not isinstance(time_delta, datetime.timedelta):
        raise TypeError(
            '%s type invalid for %s' % (type(time_delta), time_delta))

    if not isinstance(failed_threshold, int):
        raise TypeError(
            '%s type invalid for %s' % (type(failed_threshold),
                                        failed_threshold))

    return WinlogbeatHost.objects.\
        filter(enabled=True, winlogevent__created_on__gt=now - time_delta).\
        annotate(
            failed_events=Count(
                'winlogevent__event_state',
                filter=Q(winlogevent__event_state__iexact='failed'))).\
        filter(failed_events__gte=failed_threshold).\
        annotate(
            failed_threshold=Value(
                failed_threshold, output_field=BigIntegerField())).\
        annotate(measured_now=Value(now, output_field=CharField())).\
        annotate(
            measured_over=Value(time_delta, output_field=DurationField())).\
        order_by('site__site')


def get_failed_events(now=None, time_delta=None, site=None, host_name=None):
    """
    :returns: a :class:`django.db.models.query.QuerySet` containing detailed data
        about failed `ControlUp` logon events

        The :class:`django.db.models.query.QuerySet` is based on the
        :class:`citrus_borg.models.WinlogbeatHost` model and on the
        :class:`citrus_borg.models.WinlogEvent` model and is `annotated
        <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
        with the event counts (`failed` events and `successful` events)

    :arg datetime.datetime now: the initial moment

        By default the initial moment is the value returned by
        :meth:`django.utils.timezone.now`

    :arg datetime.timedelta time_delta: the time interval to consider

        By default, this will be retrieved from the dynamic preference
        `Logon reporting period
        <../../../admin/dynamic_preferences/globalpreferencemodel/?q=logon_report_period>`__

    :arg str site: if present, filter the data that will be returned by `site`,
        otherwise return data for all known sites



    :arg str host_name: if present, filter the data that will be returned by
        'host_name`, otherwise return data for all known hosts

        Be careful when using the `site` and `host_name` arguments together.
        It is possible to come up with a combination of values for which
        no data can be returned (one filters by a host that lives at a site
        that was filtered out already). This function considers such a
        combination valid and will happily return an empty
        :class:`django.db.models.query.QuerySet` when invoked with such a
        combination

    :raises: :exc:`TypeError` if the `now` argument or the `time_delta` do not
        satisfy type requirements

    """
    if now is None:
        now = timezone.now()

    if time_delta is None:
        time_delta = get_preference('citrusborglogon__logon_report_period')

    if not isinstance(now, datetime.datetime):
        raise TypeError('%s type invalid for %s' % (type(now), now))

    if not isinstance(time_delta, datetime.timedelta):
        raise TypeError(
            '%s type invalid for %s' % (type(time_delta), time_delta))

    queryset = _by_site_host_hour(
        now=now, time_delta=time_delta, site=site, host_name=host_name,
        logon_alert_threshold=1, ux_alert_threshold=None,
        include_event_counts=True, include_ux_stats=False,
        group_by=GroupBy.NONE)

    queryset = queryset.order_by('-winlogevent__created_on')

    return queryset


def get_failed_ux_events(
        now=None, time_delta=None, site=None, host_name=None,
        ux_alert_threshold=None):
    """
    :returns: a :class:`django.db.models.query.QuerySet` containing detailed data
        about `ControlUp` logon events with timings that do not satisfy user
        response time requirements

        The :class:`django.db.models.query.QuerySet` is based on the
        :class:`citrus_borg.models.WinlogbeatHost` model and on the
        :class:`citrus_borg.models.WinlogEvent` model and is `annotated
        <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
        with the event timing stats

    :arg datetime.datetime now: the initial moment

        By default the initial moment is the value returned by
        :meth:`django.utils.timezone.now`

    :arg datetime.timedelta time_delta: the time interval to consider

        By default, this will be retrieved from the dynamic preference
        `User experience reporting period
        <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ux_reporting_period>`__

    :arg str site: if present, filter the data that will be returned by `site`,
        otherwise return data for all known sites



    :arg str host_name: if present, filter the data that will be returned by
        'host_name`, otherwise return data for all known hosts

        Be careful when using the `site` and `host_name` arguments together.
        It is possible to come up with a combination of values for which
        no data can be returned (one filters by a host that lives at a site
        that was filtered out already). This function considers such a
        combination valid and will happily return an empty
        :class:`django.db.models.query.QuerySet` when invoked with such a
        combination

    :arg datetime.timedelta ux_alert_threshold: the user response time failure
        threshold

        By default, this will be retrieved from the dynamic preference
        `User experience alert threshold
        <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ux_alert_threshold>`__

    :raises: :exc:`TypeError` if the `now` argument, the `time_delta` or the
        `ux_alert_threshold` arguments do not satisfy type requirements

    """
    if now is None:
        now = timezone.now()

    if time_delta is None:
        time_delta = get_preference('citrusborgux__ux_reporting_period')

    if ux_alert_threshold is None:
        ux_alert_threshold = get_preference(
            'citrusborgux__ux_alert_threshold')

    if not isinstance(now, datetime.datetime):
        raise TypeError('%s type invalid for %s' % (type(now), now))

    if not isinstance(time_delta, datetime.timedelta):
        raise TypeError(
            '%s type invalid for %s' % (type(time_delta), time_delta))

    if not isinstance(ux_alert_threshold, datetime.timedelta):
        raise TypeError(
            '%s type invalid for %s' % (type(ux_alert_threshold),
                                        ux_alert_threshold))

    queryset = _by_site_host_hour(
        now=now, time_delta=time_delta, site=site, host_name=host_name,
        logon_alert_threshold=None, ux_alert_threshold=ux_alert_threshold,
        include_event_counts=False, include_ux_stats=True,
        group_by=GroupBy.NONE)

    queryset = queryset.order_by('-winlogevent__created_on')

    return queryset
