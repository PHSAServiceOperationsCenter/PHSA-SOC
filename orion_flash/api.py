"""
.. _api:

api module for the orion_flash app

:module:    p_soc_auto.orion_flash.api

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Mar. 6, 2019

"""
import socket

from django.conf import settings
from django.db.models import F, Value, TextField, URLField
from django.db.models.functions import Cast, Concat
from django.db.models.query import QuerySet

from citrus_borg.locutus.communication import (
    get_dead_bots as _get_dead_bots, raise_failed_logins_alarm,
    raise_ux_alarm, GroupBy,
)
from citrus_borg.dynamic_preferences_registry import get_preference


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


def get_dead_bots(
        now=None, time_delta=None,
        annotate_url=True, annotate_details_url=True, **details):
    """
    get the dead bots and annotate each of them with an url to the
    admin change form for the bot and with the amdin link for the events
    coming from this bot
    """
    queryset = _get_dead_bots(now, time_delta)

    if annotate_url:
        queryset = url_annotate(queryset)

    if annotate_details_url:
        queryset = details_url_annotate(queryset, **details)

    return queryset


def get_failed_logons(
        now=None, time_delta=None, failed_threshold=None,
        annotate_url=True, annotate_details_url=True, **details):
    """
    get the failed login counts that are raising alerts
    """
    queryset = raise_failed_logins_alarm(now, time_delta, failed_threshold)

    if annotate_url:
        queryset = url_annotate(queryset)

    if annotate_details_url:
        queryset = details_url_annotate(queryset, **details)

    return queryset


def get_ux_alarms(  # pylint: disable=too-many-arguments
        now=None,  group_by=GroupBy.NONE,
        time_delta=get_preference('citrusborgux__ux_alert_interval'),
        ux_alert_threshold=get_preference('citrusborgux__ux_alert_threshold'),
        annotate_url=True, annotate_details_url=True, **details):
    """
    get the user experience alert data
    """
    queryset = raise_ux_alarm(
        now=now, group_by=group_by, time_delta=time_delta,
        ux_alert_threshold=ux_alert_threshold)

    if annotate_url:
        queryset = url_annotate(queryset)

    if annotate_details_url:
        queryset = details_url_annotate(queryset, **details)

    return queryset
