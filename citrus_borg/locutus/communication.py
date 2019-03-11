"""
.. _communication:

functions and classes for generating data from the citrus_borg app

:module:    citrus_borg.locutus.communication

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    nov. 128, 2018


notes for filtering

WinlogEvent.objects.filter(
    event_state__iexact='failed',
    created_on__gt=timezone.now() - timezone.timedelta(minutes=1000)).count()

group this by host and count for each host
send one report like this for a fixed period of time

and raise alarm if for given timedelta, count per host is greater than X


repeat the same thing but per site instead of per host


- other stuff

for the last x minutes get the hosts with pass and see if there is a diff
with the hosts from the host model
looks like if item not in list(distinct) and item in host model, append to
missing and send email for each missing

same thing but for sites

and same thing for brokers

"""
import datetime

from enum import Enum

from django.db.models import (
    Count, Q, Min, Max, Avg, StdDev, DurationField, Value,
)
from django.db.models.functions import TruncHour, TruncMinute, Now
from django.utils import timezone

from citrus_borg.models import (
    WinlogEvent, WinlogbeatHost, KnownBrokeringDevice, BorgSite,
)
from citrus_borg.dynamic_preferences_registry import get_preference


class GroupBy(Enum):
    """
    enumeration for specifying the group by time sequence details
    """
    NONE = None
    HOUR = 'hour'
    MINUTE = 'minute'


def get_dead_bots(now=None, time_delta=None):
    """
    get the bot hosts not seen during the interval defined by the arguments

    :arg now: the initial date-time moment
    :arg time_delta: the time interval to consider

    :returns: a django queryset with the bots qualifying or ``None``

    :raises: :exception:`<TypeError>` if the arguments are not of valid
             `datetime` types

    grrrr, queryset.difference(*querysets) doesn't work on mariadb

    we need to do list=list - list or something

    use? https://mariadb.com/kb/en/library/timediff/ to annotate with the diff
    on the queryset?

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

    dead_bots = WinlogbeatHost.objects.filter(host_name__in=list(dead_bots))

    dead_bots = dead_bots.\
        annotate(not_seen_gt=Value(time_delta, output_field=DurationField()))

    if dead_bots.exists():
        dead_bots = dead_bots.order_by('last_seen')

    return dead_bots


def get_dead_brokers(now=None, time_delta=None):
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
    data source for the bot reports

    :returns: a queryset with the list of bots ordered by site, grouped by
              hour, and including counts for failed and successful logon
              events

    :arg now:
    :arg time_delta:
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
    :returns:

        a queryset with rows where the average storefront connection or the
        average logon duration are greater than or equal to the value of
        :ux_alert_threshold


    """
    try:
        queryset = _by_site_host_hour(
            now=now, time_delta=time_delta, site=site, host_name=host_name,
            group_by=group_by, ux_alert_threshold=ux_alert_threshold,
            include_event_counts=include_event_counts)
    except Exception as error:
        raise error

    return queryset.order_by(
        'site__site', 'host_name', '-avg_logon_time', '-minute',
        '-avg_storefront_connection_time')
# pylint: enable=too-many-arguments


def _include_event_counts(queryset):
    """
    annotate a queryset with the counts for event states
    """
    return queryset.annotate(
        failed_events=Count(
            'winlogevent__event_state',
            filter=Q(winlogevent__event_state__iexact='failed'))).\
        annotate(
            successful_events=Count(
                'winlogevent__event_state',
                filter=Q(winlogevent__event_state__iexact='successful')))


def _include_ux_stats(queryset):
    """
    annotate a queryset with min, avg, max, and stddev for subevent duration
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
            min_logon_time=Min('winlogevent__receiver_startup_duration')).\
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
    :returns:

        a queryset grouped by site and host

        if requested:

        *    the queryset will be grouped by hourly increments

        *    the queryset will include counts of failed and successful logins

        *    the queryset will include user experience estimates based on
             the min, max, and avg valaues of the durations associated with
             each subevent (connect to storefront, start receiver,
             logon achieved, connection achieved)

        *    the queryset will be filtered on the failed event count using
             the gte operator

        *    the queryset will be filtered on the average storefront connection
             duration or the average logon connection duration using a
             (gte or gte) operator combination

    :rtype: `<django.db.models.query.QuerySet>`

    :arg `datetime.datetime` now: the reference time point for the report

    :arg `datetime.timedelta` time_delta:

        the period to report upon, measured backwards from :now:

    :arg str site:

        filter by site; default ``None`` meaning return data for all sites

    :arg str host_name:

        filter by host name; default ``None`` meaning return data for all the
        bots

    :arg int logon_alert_trehsold:

        only return rows where the failed event count is gte to this
        argument

    :arg `datetime.timedelta` ux_alert_threshold:

        only return rows where the average storefront connection or the
        average logon duration are gte to this argument

    :arg bool include_event_counts:

        include count for event states (successful and failed)

    :arg bool include_ux_stats:

        include min, max, avg, and stdev for all the subevent durations
        provided by ControlUp, default ``True``

    :arg group_by:

        the kind of sequence to use, if any, when grouping by time,
        default is by hour

    :argtype group_by: :enum:`<GroupBy>`

    :raises:

        :exception:`<TypeError>` if :arg:`<now>` is not a
        `datetime.datetime` instance

        :exception:`<TypeError>` if  :arg:`<time_delta>` or
        :arg:`<ux-alert_threshold>` are not `datetime.timedelta` instances

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

    if host_name:
        queryset = queryset.filter(host_name__iexact=host_name)

    queryset = queryset.values('site__site').values('host_name')

    queryset = _group_by(queryset, group_by)

    if include_event_counts:
        queryset = _include_event_counts(queryset)

    if include_ux_stats:
        queryset = _include_ux_stats(queryset)

    if logon_alert_threshold:
        queryset = queryset.filter(failed_events__gt=logon_alert_threshold)

    if ux_alert_threshold:
        queryset = queryset.\
            filter(
                Q(avg_storefront_connection_time__gt=ux_alert_threshold) |
                Q(avg_logon_time__gt=ux_alert_threshold))

    return queryset
# pylint: enable=too-many-arguments,too-many-branches


def _group_by(queryset, group_by=GroupBy.NONE):
    if group_by == GroupBy.HOUR:
        return queryset.\
            annotate(hour=TruncHour('winlogevent__created_on')).values('hour')

    if group_by == GroupBy.MINUTE:
        return queryset.\
            annotate(minute=TruncMinute('winlogevent__created_on')).\
            values('minute')

    return queryset


def login_states_by_site_host_hour(
        now=None,
        time_delta=get_preference(
            'citrusborgevents__ignore_events_older_than'),
        site=None, host_name=None):
    """
    :returns:

        a queryset grouped by site, host, and time in hour increments

        the queryset is sorted by site, host, and time descending.

    :rtype: `<django.db.models.query.QuerySet>`

    :arg `datetime.datetime` now:

        the reference time point for the report, by default it is the moment
        returned by :function:`<django.utils.timezone.now>`

    :arg `datetime.timedelta` time_delta:

        the period to report upon, measured backwards from :now:, the efault
        is picked from the django settings file, specifically from
        `settings.CITRUS_BORG_IGNORE_EVENTS_OLDER_THAN`

    :arg str site:

        filter by site; default ``None`` meaning return data for all sites

    :arg str host_name:

        filter by host name; default ``None`` meaning return data for all the
        bots

    :raises:

        :exception:`<Exception>` if :arg:`<now>` or :arg:`<time_delta>` are
        not of the specified types
    """
    try:
        queryset = _by_site_host_hour(now, time_delta, site, host_name)
    except Exception as error:
        raise error

    return queryset.order_by('site__site', 'host_name', '-hour')


def raise_failed_logins_alarm(
        now=None, time_delta=None, failed_threshold=None):
    """
    return a queryset of Citrix bots for which the number of failed logon
    events over the specified period of time exceeds the failed threshold

    :arg now: the referencce time moment,
              by default `django.utils.timezone.now`

    :arg time_delta: the time interval to be considered, by default
                     `settings.CITRUS_BORG_FAILED_LOGON_ALERT_INTERVAL`

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
        order_by('site__site')


def get_failed_events(now=None, time_delta=None, site=None, host_name=None):
    """
    :returns: a queryset extracted from :class:`<models.WinlogEvent>`
    :rtype: `<django.db.models.query.QuerySet>`

    :arg `datetime.datetime` now:

        the reference time point for the report; default is ``None`` in which
        case the value returned by the django equivalent of
        `datetime.dateime.now` is used

    :arg `datetime.timedelta` time_delta:

        the period to report upon, measured backwards from :now:; default is
        ``None`` in which case a default value configured in
        :module:`<settings>` is used

    :arg str site:

        filter by site; default ``None`` meaning return data for all sites

    :arg str host_name:

        filter by host name; default ``None`` meaning return data for all the
        bots

    :raises:

        :exception:`<TypeError>` if :arg:`<now>` is not a
        `datetime.datetime` instance

        :exception:`<TypeError>` if  :arg:`<time_delta>` is not
        `datetime.timedelta` instances


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

    queryset = WinlogEvent.objects.\
        filter(created_on__gt=now - time_delta).\
        exclude(event_state__iexact='successful')

    if site:
        queryset = queryset.filter(source_host__site__site__iexact=site)

    if host_name:
        queryset = queryset.filter(source_host__host_name__iexact=host_name)

    queryset = queryset.order_by('-created_on')

    return queryset
