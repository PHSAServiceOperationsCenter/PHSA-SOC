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
        raise TypeError('%s type invalid for %s' % (type(now), now))

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
        raise TypeError('%s type invalid for %s' % (type(now), now))

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
        raise TypeError('%s type invalid for %s' % (type(now), now))

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
