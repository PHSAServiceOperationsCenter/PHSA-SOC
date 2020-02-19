"""
.. _tasks:

celery tasks for the orion_flash app

:module:    orion_flash.tasks

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from celery import shared_task, group  # @UnresolvedImport
from celery.utils.log import get_task_logger  # @UnresolvedImport
from django.apps import apps

from ssl_cert_tracker.lib import (
    is_not_trusted, expires_in, has_expired,  # @UnresolvedImport
    is_not_yet_valid,  # @UnresolvedImport
)
from ssl_cert_tracker.models import SslCertificate  # @UnresolvedImport
from p_soc_auto_base import utils as base_utils

from .api import get_dead_bots, get_failed_logons, get_ux_alarms


LOG = get_task_logger(__name__)

KNOWN_SSL_DESTINATIONS = [
    'orion_flash.expiressoonsslalert', 'orion_flash.untrustedsslalert',
    'orion_flash.expiredsslalert', 'orion_flash.invalidsslalert',
]

KNOWN_BORG_DESTINATIONS = [
    'orion_flash.deadcitrusbotalert', 'orion_flash.citrusborgloginalert',
    'orion_flash.citrusborguxalert',
]


@shared_task(queue='orion_flash')
def purge_ssl_alerts():
    """
    go through the model defined by :arg:`<source>` and verify that each
    instance still matches to a certificate in the
    :class:`<ssl_cert_tracker.models.SslCertificate>`

    if it doesn't, delete the instance
    """
    delete_info = []
    for data_source in KNOWN_SSL_DESTINATIONS:

        model = apps.get_model(data_source)
        for alert in model.objects.values('orion_node_id', 'orion_node_port'):
            deleted = 0
            if not SslCertificate.objects.filter(
                    orion_id=alert['orion_node_id'],
                    port__port=alert['orion_node_port']).exists():

                deleted = model.objects.filter(
                    orion_node_id=alert['orion_node_id'],
                    orion_node_port=alert['orion_node_port']
                ).all().delete()

            delete_info.append(
                'deleted orphaned %s alerts from %s' % (deleted, data_source))

    return delete_info


@shared_task(
    task_serializer='pickle', result_serializer='pickle', rate_limit='2/s',
    queue='orion_flash')
def create_or_update_orion_alert(destination, qs_rows_as_dict):
    """
    create orion alert instances

    """
    return apps.get_model(destination).create_or_update(qs_rows_as_dict)


@shared_task(
    task_serializer='pickle', result_serializer='pickle', queue='orion_flash')
def refresh_ssl_alerts(destination, **kwargs):
    """
    dispatch alert data to orion auxiliary ssl alert models
    """
    if destination.lower() not in KNOWN_SSL_DESTINATIONS:
        raise base_utils.UnknownDataTargetError(
            '%s is not known to this application' % destination)

    apps.get_model(destination).objects.all().delete()

    data_rows = get_data_for(destination, **kwargs).\
        values(*base_utils.get_queryset_values_keys(
            apps.get_model(destination)))

    if not data_rows:
        return 'no data'

    LOG.debug('retrieved %s new/updated data rows for destination %s.'
              ' first row sample: %s',
              len(data_rows), destination, data_rows[0])

    group(create_or_update_orion_alert.s(destination, data_row).
          set(serializer='pickle')
          for data_row in data_rows)()

    msg = 'refreshing data in %s from %s entries' % (destination,
                                                     len(data_rows))
    return msg


# TODO refactor refresh methods into a single one
@shared_task(
    task_serializer='pickle', result_serializer='pickle', queue='orion_flash')
def refresh_borg_alerts(destination, **kwargs):
    """
    dispatch alert data to orion auxiliary citrix bot alert models
    """
    if destination.lower() not in KNOWN_BORG_DESTINATIONS:
        raise base_utils.UnknownDataTargetError(
            '%s is not known to this application' % destination)

    deleted = apps.get_model(destination).objects.all().delete()
    LOG.debug(
        'purged %s records from %s',
        deleted, apps.get_model(destination)._meta.model_name)

    data_rows = get_data_for(destination, **kwargs).\
        values(*base_utils.get_queryset_values_keys(
            apps.get_model(destination)))

    if not data_rows:
        return 'no data'

    LOG.debug('retrieved %s new/updated data rows for destination %s.'
              ' first row sample: %s',
              len(data_rows), destination, data_rows[0])

    group(create_or_update_orion_alert.s(destination, data_row).
          set(serializer='pickle')
          for data_row in data_rows)()

    msg = 'refreshing data in %s from %s entries' % (destination,
                                                     len(data_rows))
    return msg


def get_data_for(destination, **kwargs):
    """
    Get the required queryset.

    :arg str destination: The name of the alert to get data for.

    :arg kwargs: Named arguments for the function used to retrieve the data.
        See the specific functions for details (review code for function names).

    :raises: :exception:`ValueError` If destination is not one of:
        orion_flash.expiressoonsslalert, orion_flash.untrustedsslalert,
        orion_flash.expiredsslalert, orion_flash.invalidsslalert,
        orion_flash.deadcitrusbotalert, orion_flash.citrusborgloginalert,
        orion_flash.citrusborguxalert

    :raises: Errors varying by function if the arguments are passed in
        incorrectly.
    """
    dest_to_f = {
        'orion_flash.expiressoonsslalert': expires_in,
        'orion_flash.untrustedsslalert': is_not_trusted,
        'orion_flash.expiredsslalert': has_expired,
        'orion_flash.invalidsslalert': is_not_yet_valid,
        'orion_flash.deadcitrusbotalert': get_dead_bots,
        'orion_flash.citrusborgloginalert': get_failed_logons,
        'orion_flash.citrusborguxalert': get_ux_alarms,
    }

    try:
        dest_to_f[destination](**kwargs)
    except KeyError:
        raise ValueError('there is no known data source for destination %s'
                         % destination)
