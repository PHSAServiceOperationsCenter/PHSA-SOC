"""
.. _queries:

:module:    mail_collector.queries

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Jun. 11, 2019

Query functions for the :ref:`Mail Collector Application`
"""
import datetime

from django.apps import apps
from django.db.models import Max
from django.db.models.query import QuerySet

from citrus_borg.dynamic_preferences_registry import get_preference
from citrus_borg.locutus.communication import GroupBy, _group_by
from mail_collector.models import (
    ExchangeServer, ExchangeDatabase, MailBotLogEvent, MailBotMessage,)
from p_soc_auto_base.utils import (
    MomentOfTime, get_base_queryset,
    url_annotate as _url_annotate,
)


def dead_bodies(data_source, filter_exp,
                not_seen_after=None, url_annotate=False, **base_filters):
    """
    :returns: :class:`django.db.models.Queryset` objects that are filtered on
        :class:`django.db.models.DateTimeField` fields

    :arg data_source: the data source used to populate the queryset

            Either a :class:`django.db.models.Queryset` object or a :class:`str`
            in 'app_label.modelname' format

    :arg str filter_exp: the field and lookup to use for filtering

        For example, 'last_updated__lte' will filter on a field named
        last_updated using a less than or equal lookup

    :arg not_seen_after:

        the time interval required to buid the filter parameter value

        It can be a :class:`datetime.timedelta` object or a :class:`dict`
        that can be used to construct a :class:`datetime.timedelta` object.

        Default: ``None``. When ``None``, the value is picked up from
        :class:`citrus_borg.dynamic_properties_registry.ExchangeServerError`.

    :arg bool url_annotate: do we also add the absolute url for each object?

    :arg \*\*base_filters: optional django lookups for the queryset

    :raises:

        :exc:`TypeError` if the not_seen_after argument is of types other
        than :class:`datetime.timedelta` object, :class:`dict`
        that can be used to construct a :class:`datetime.timedelta` object,
        or ``None``
    """
    if not_seen_after is None:
        not_seen_after = MomentOfTime.past(
            time_delta=get_preference('exchange__server_error'))

    if isinstance(not_seen_after, dict):
        not_seen_after = MomentOfTime.past(**not_seen_after)

    if not isinstance(not_seen_after, datetime.datetime):
        raise TypeError(
            'Invalid object type %s, was expecting datetime'
            % type(not_seen_after))

    if not isinstance(data_source, QuerySet):
        queryset = get_base_queryset(data_source, **base_filters)

    queryset = queryset.filter(**{filter_exp: not_seen_after})

    if url_annotate:
        queryset = _url_annotate(queryset)

    return queryset


def dead_mail_sites(not_seen_after=None):
    """
    :returns:

        :class:`django.db.models.Queryset` objects based on 
        :class:`mail_collector.models.MailHost` that
        represent sites from where exchange requests have not
        been observed for the duration specified in the argument

    This query function must filter on an aggregated annotation.
    There may be multiple bots on any site and the site can only be
    considered down if all its bots are down. We must filter against the
    bot most recently seen for each site.

    :param not_seen_after: the time interval required to buid the filter
        parameter value

        It can be a :class:`datetime.timedelta` object or a :class:`dict`
        that can be used to construct a :class:`datetime.timedelta` object.

        Default: ``None``. When ``None``, the value is picked up from
        :class:`citrus_borg.dynamic_properties_registry.ExchangeServerError`

    :raises:

        :exc:`TypeError` if the not_seen_after argument is of types other
        than :class:`datetime.timedelta` object, :class:`dict`
        that can be used to construct a :class:`datetime.timedelta` object,
        or ``None``
    """
    if not_seen_after is None:
        not_seen_after = MomentOfTime.past(time_delta=not_seen_after)

    if isinstance(not_seen_after, dict):
        not_seen_after = MomentOfTime.past(**not_seen_after)

    if not isinstance(not_seen_after, datetime.datetime):
        raise TypeError(
            'Invalid object type %s, was expecting datetime'
            % type(not_seen_after))

    queryset = get_base_queryset('mail_collector.mailhost', enabled=True)

    queryset = queryset.values('site__site').\
        annotate(most_recent=Max('excgh_last_seen')).\
        filter(most_recent__lte=not_seen_after).\
        order_by('site__site', '-most_recent')

    return queryset


"""
core query for report:

In [11]: MailBotMessage.objects.values('sent_from','sent_to','received_from','received_by','event__event_type',
    ...: 'event__event_status','event__event_registered_on')[1]
Out[11]:
{'sent_from': 'z-spexcm001-db01001@phsa.ca',
 'sent_to': 'z-spexcm001-db01001@phsa.ca',
 'received_from': 'svc_SOCmailbox@phsa.ca',
 'received_by': 'z-spexcm001-db01001@phsa.ca',
 'event__event_type': 'receive',
 'event__event_status': 'PASS',
 'event__event_registered_on': datetime.datetime(2019, 6, 17, 21, 40, 49, 719579, tzinfo=<UTC>)}

In [12]:

using dead_bodies

 qs=dead_bodies('mail_collector.mailbotmessage',
                'event__event_registered_on__gte',
                not_seen_after={'days': 30},
                url_annotate=False,
                event__event_type='receive')
                
                other filters to use:
                event__event_source_host__site__site__iexact=site_to_search
                event__event_source_host__host_name__iexact=host_to_search
                sent_from__icontains=exchange_server
                sent_from__icontains=exchange_database
                event__event_status__iexact='fail'|'pass'


 qs.values('sent_from',
           'sent_to',
           'received_from',
           'received_by',
           'event__event_status',
           'event__event_registered_on','event__source_host__site__site')
           
which begs the question: how do we deal with log events instead of
log mail messages?
duh... use mailbotlogevent as the source and add a filter for
mailbotmessage__isnull. it will also work with hasattr but then we need
a different template for the output.
we can use a qs.union() as well? nope, there is something that i am not
understanding with the damn union.
"""
