"""
.. _api:

api module for the orion_flash app

:module:    p_soc_auto.orion_flash.api

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from citrus_borg.locutus.communication import (
    get_dead_bots as _get_dead_bots, raise_failed_logins_alarm,
    raise_ux_alarm, GroupBy,
)
from citrus_borg.dynamic_preferences_registry import get_preference
from p_soc_auto_base import utils as base_utils


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
        queryset = base_utils.url_annotate(queryset)

    if annotate_details_url:
        queryset = base_utils.details_url_annotate(queryset, **details)

    return queryset


def get_failed_logons(
        now=None, time_delta=None, failed_threshold=None,
        annotate_url=True, annotate_details_url=True, **details):
    """
    get the failed login counts that are raising alerts
    """
    queryset = raise_failed_logins_alarm(now, time_delta, failed_threshold)

    if annotate_url:
        queryset = base_utils.url_annotate(queryset)

    if annotate_details_url:
        queryset = base_utils.details_url_annotate(queryset, **details)

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
        queryset = base_utils.url_annotate(queryset)

    if annotate_details_url:
        queryset = base_utils.details_url_annotate(queryset, **details)

    return queryset
