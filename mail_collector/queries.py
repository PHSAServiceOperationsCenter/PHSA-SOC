"""
.. _queries:

query classes and functions for the mail_collector app

:module:    mail_collector.queries

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Jun. 11, 2019

"""
import datetime

from django.apps import apps
from django.db.models import Max
from django.db.models.query import QuerySet

from mail_collector.models import (
    ExchangeServer, ExchangeDatabase, MailBotLogEvent, MailBotMessage,)

from citrus_borg.dynamic_preferences_registry import get_preference
from citrus_borg.locutus.communication import GroupBy, _group_by
from orion_flash.api import (
    url_annotate as _url_annotate,
    details_url_annotate as _details_url_annotate,
)
from p_soc_auto_base.utils import MomentOfTime, get_base_queryset


def dead_bodies(data_source, filter_exp,
                not_seen_after=None, url_annotate=False, **base_filters):
    """
    return instances not seen before a moment in time

    :param data_source:
        a queryset or the data source in 'app_label.modelname' format
    :param filter_exp: the field and lookup to use for filtering

        for example, 'last_updated__lte' will filter on a field named
        last_updated using a less than or equal lookup
    :type filter_exp: str
    :param not_before: the moment in time used for filtering
    :type not_before: datetime.datetime
    :param url_annotate: do we also add the absolute url for each object?
    :type url_annotate: bool
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


"""
for MailSite last seen do this trick:

 MailHost.objects.annotate(most_recent=Max('excgh_last_seen')).\
 filter(most_recent__lte=timezone.now()-get_preference('exchange__server_error')).\
 values('site__site','most_recent')
"""
