"""
ldap_probe.tasks
-----------------

This module contains the `Celery tasks
<https://docs.celeryproject.org/en/latest/userguide/tasks.html>`__
used by the :ref:`Domain Controllers Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:contact:    daniel.busto@phsa.ca

:updated:    Nov. 19, 2019

"""
from django.utils import timezone

from celery import shared_task, group
from celery.utils.log import get_task_logger

from ldap_probe import ad_probe, models
from citrus_borg.dynamic_preferences_registry import get_preference
from p_soc_auto_base import utils

LOG = get_task_logger(__name__)
"""default :class:`logger.Logging` instance for this module"""


@shared_task(queue='ldap_probe', rate_limit='5/s')
def probe_ad_controller(ad_model=None, ad_pk=None, logger=LOG):
    """
    probe the domain and save the AD monitoring data

    :arg str ad_model: the specification for the
        :class:`django.db. models.Model` containing the `AD` specification

    :arg int ad_pk: the primary key of the
        :class:`django.db.modles.Model` instance that contains the
        AD controller  node information

    :arg logger: the logger instance
    :type logger: :class:`loggingLogger`

    :returns: the return of
        :meth:`ldap_probe.models.LdapProbeLog.create_from_probe`

    :raises: :exc:`exceptions.Exception`
    """
    try:
        ad_model = utils.get_model(ad_model)
    except utils.UnknownDataTargetError as error:
        raise error

    if not isinstance(ad_pk, int):
        raise TypeError(f'Bad dog! No {type(ad_pk)} type biscuit for you')

    try:
        created = models.LdapProbeLog.create_from_probe(
            ad_probe.ADProbe(
                ad_model.objects.get(ad_pk))
        )
    except Exception as error:
        logger.error(error)
        raise error

    logger.debug(created)

    return created


@shared_task(queue='ldap_probe')
def bootstrap_ad_probes(data_sources=None):
    """
    launch a separate probing task for each `AD` controller extracted
    from the arguments

    This task uses the `Celery Canvas Group primitive
    <https://docs.celeryproject.org/en/latest/userguide/canvas.html#groups>`__
    to launch multiple parallel instances of the :meth:`probe_ad_controller`
    task.

    :arg data_sources: the name(s) of the :class:`Django model(s)
        <django.db.models.Model>` that store `AD` controller information

        This item in this argument must be represented using the
        `app_label.model_name` convention. The argument can be a
        :class:`list` or a :class:`tuple`, or a :class:`str` that separates
        each entry using a comma (,) character.

        By default this argument points to the models defined under
        :class:`ldap_probe.models.OrionADNode` and
        :class:`ldap_probe.models.NonOrionADNode`

    :returns: a `CR` separated string containing the name of each data
        source and the number of `AD` controllers defined under said source
    :rtype: str
    """
    if data_sources is None:
        data_sources = 'ldap_probe.OrionADNode,ldap_probe.NonOrionADNode'

    if not isinstance(data_sources, (list, tuple)):
        data_sources = data_sources.split(',')

    results = []
    for data_source in data_sources:
        pk_list = utils.get_pk_list(
            utils.get_base_queryset(data_source, enabled=True))
        group(probe_ad_controller.s(data_source, ad_pk) for ad_pk in pk_list)()
        results.append(
            f'Will probe {len(pk_list)} AD controllers from {data_source}.')

    return '\n'.join(results)


@shared_task(queue='data_prune')
def expire_entries(data_source=None, **age):
    """
    """
    if data_source is None:
        data_source = 'ldap_probe.LdapProbeLog'

    try:
        data_source = utils.get_model(data_source)
    except utils.UnknownDataTargetError as error:
        raise error

    if not hasattr(data_source, 'created'):
        raise TypeError(
            f'no age tracking field in {data_source._meta.model_name}')

    if not age:
        time_delta = get_preference('ldap_expire_after')
