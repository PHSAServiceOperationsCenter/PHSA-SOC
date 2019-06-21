"""
.. _tasks:

celery tasks for the orion_flash app

:module:    orion_flash.tasks

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Feb. 1, 2019

"""
from django.apps import apps

from celery import shared_task, group  # @UnresolvedImport
from celery.utils.log import get_task_logger  # @UnresolvedImport


from ssl_cert_tracker.lib import (
    is_not_trusted, expires_in, has_expired,  # @UnresolvedImport
    is_not_yet_valid,  # @UnresolvedImport
)
from ssl_cert_tracker.models import SslCertificate  # @UnresolvedImport

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


class UnknownDataTargetError(Exception):
    """
    raise when trying to upload to an unknown data model
    """


class UnknownDataSourceError(Exception):
    """
    raise when we don't know where the data is supposed to come from
    """


class DataTargetFieldsAttributeError(Exception):
    """
    raise when the target model doesn't have a qs_fields attribute
    """


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

        model = get_model(data_source)
        for alert in model.objects.values('orion_node_id', 'orion_node_port'):
            deleted = 0
            if not SslCertificate.objects.filter(
                    orion_id=alert['orion_node_id'],
                    port__port=alert['orion_node_port']).exists():

                deleted = model.objects.filter(
                    orion_node_id=alert['orion_node_id'],
                    orion_node_port=alert['orion_node_port']
                ).objects().all().delete()

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
    try:
        return get_model(destination).create_or_update(qs_rows_as_dict)
    except Exception as err:
        raise err


@shared_task(
    task_serializer='pickle', result_serializer='pickle', queue='orion_flash')
def refresh_ssl_alerts(destination, logger=LOG, **kwargs):
    """
    dispatch alert data to orion auxiliary ssl alert models
    """
    if destination.lower() not in KNOWN_SSL_DESTINATIONS:
        raise UnknownDataTargetError(
            '%s is not known to this application' % destination)

    data_rows = get_data_for(destination, **kwargs).\
        values(*get_queryset_values_keys(get_model(destination)))

    if not data_rows:
        return 'no data'

    logger.debug('retrieved %s new/updated data rows for destination %s.'
                 ' first row sample: %s',
                 len(data_rows), destination, data_rows[0])

    group(create_or_update_orion_alert.s(destination, data_row).
          set(serializer='pickle')
          for data_row in data_rows)()

    msg = 'refreshing data in %s from %s entries' % (destination,
                                                     len(data_rows))
    return msg


@shared_task(
    task_serializer='pickle', result_serializer='pickle', queue='orion_flash')
def refresh_borg_alerts(destination, logger=LOG, **kwargs):
    """
    dispatch alert data to orion auxiliary citrix bot alert models

    i know, i know, these refresh functions need to be refactored into
    a single one. but there is an argument to be made for keeping the
    periodic task definition simple
    """
    if destination.lower() not in KNOWN_BORG_DESTINATIONS:
        raise UnknownDataTargetError(
            '%s is not known to this application' % destination)

    deleted = get_model(destination).objects.all().delete()
    logger.debug(
        'purged %s records from %s',
        deleted, get_model(destination)._meta.model_name)

    data_rows = get_data_for(destination, **kwargs).\
        values(*get_queryset_values_keys(get_model(destination)))

    if not data_rows:
        return 'no data'

    logger.debug('retrieved %s new/updated data rows for destination %s.'
                 ' first row sample: %s',
                 len(data_rows), destination, data_rows[0])

    group(create_or_update_orion_alert.s(destination, data_row).
          set(serializer='pickle')
          for data_row in data_rows)()

    msg = 'refreshing data in %s from %s entries' % (destination,
                                                     len(data_rows))
    return msg


def get_model(destination):
    """
    get the model where the data is to be saved
    """
    try:
        return apps.get_model(*destination.split('.'))
    except Exception as err:
        raise UnknownDataTargetError from err


def get_queryset_values_keys(model):
    """
    this function returns a list of keys that will be passed to
    :method:`<django.db.models.query.QuerySet.values>`

    :returns: a `list of field names

        note that these field names are for the queryset, **not for the
        model that is the source of thew queryset**, because a queryset
        can contain fields defined via annotations and/or aggregations

    :raises: :exception:`<DataTargetFieldsAttributeError>`
    """
    if not hasattr(model, 'qs_fields'):
        raise DataTargetFieldsAttributeError(
            'model %s is missing the qs_fields attribute'
            % model._meta.model_name)

    return model.qs_fields


def get_data_for(destination, **kwargs):
    """
    get the queryset that we need

    pass the named arguments to the functions called to return the queryset.
    these arguments are function specific and documenting them here is not
    exactly useful

    note that the lt_days default cannot be None. it doesn't make sense to
    create alerts for certififcates that expire soon unless soon is actually
    defined. for that matter lt_days default cannot be 0 for the same reason.
    it also shouldn't be 1 but in that case it will be reset to 2 in the
    queryset function

    :raises: :exception:`<UnknownDataSourceError>`
    """
    lt_days = kwargs.get('lt_days', 2)
    app_path = kwargs.get('app_path', 'citrus_borg')
    model_path = kwargs.get('model_path', 'winlogevent')
    param_name = kwargs.get('param_name', 'source_host__host_name')
    param_lookup_name = kwargs.get('param_lookup_name', 'host_name')

    if destination in ['orion_flash.expiressoonsslalert']:
        return expires_in(lt_days=lt_days)
    if destination in ['orion_flash.untrustedsslalert']:
        return is_not_trusted(**kwargs)
    if destination in ['orion_flash.expiredsslalert']:
        return has_expired(**kwargs)
    if destination in ['orion_flash.invalidsslalert']:
        return is_not_yet_valid(**kwargs)

    if destination in ['orion_flash.deadcitrusbotalert']:
        return get_dead_bots(
            app_path=app_path, model_path=model_path, param_name=param_name,
            param_lookup_name=param_lookup_name, **kwargs)
    if destination in ['orion_flash.citrusborgloginalert']:
        return get_failed_logons(
            app_path=app_path, model_path=model_path, param_name=param_name,
            param_lookup_name=param_lookup_name, **kwargs)
    if destination in ['orion_flash.citrusborguxalert']:
        return get_ux_alarms(
            app_path=app_path, model_path=model_path, param_name=param_name,
            param_lookup_name=param_lookup_name, **kwargs)

    raise UnknownDataSourceError(
        'there is no known data source for destination %s' % destination)
