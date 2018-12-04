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

from django.conf import settings
from django.db.models import Count, Q
from django.db.models.functions import TruncHour
from django.utils import timezone

from citrus_borg.models import (
    WinlogEvent, WinlogbeatHost, KnownBrokeringDevice, BorgSite,
)


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

    """
    if now is None:
        now = timezone.now()

    if time_delta is None:
        time_delta = settings.CITRUS_BORG_DEAD_BOT_AFTER

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
    if dead_bots.exists():
        return dead_bots.order_by('last_seen')

    return None


def get_dead_brokers(now=None, time_delta=None):
    if now is None:
        now = timezone.now()

    if time_delta is None:
        time_delta = settings.CITRUS_BORG_DEAD_BORG_AFTER

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
        return dead_brokers.order_by('last_seen')

    return None


def get_dead_sites(now=None, time_delta=None):
    if now is None:
        now = timezone.now()

    if time_delta is None:
        time_delta = settings.CITRUS_BORG_DEAD_SITE_AFTER

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
        return dead_sites.order_by('winlogbeathost__last_seen')

    return None


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
        time_delta = settings.CITRUS_BORG_IGNORE_EVENTS_OLDER_THAN

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
        time_delta = settings.CITRUS_BORG_FAILED_LOGON_ALERT_INTERVAL

    if failed_threshold is None:
        failed_threshold = settings.FAILED_LOGON_ALERT_THRESHOLD

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
