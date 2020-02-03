"""
orion_integration.tasks
-----------------------

This module contains the `Celery tasks
<https://docs.celeryproject.org/en/latest/userguide/tasks.html>`__ for the
:ref:`Orion Integration Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

:updated:    Oct. 24, 2019

"""
from logging import getLogger

from requests.exceptions import HTTPError

from celery import shared_task, group
from django.apps import apps
from orion_integration.models import (
    OrionAPMApplication, OrionNodeCategory, OrionNode,
)

LOG = getLogger(__name__)


@shared_task(queue='orion', rate_limit='5/s')
def populate_from_orion():
    """
    this task will create and/or update the `Orion` data cached by the
    :ref:`Orion Integration Application`

    :returns: a list of models that were updated
    :rtype: list
    """
    ret = []
    for model in [OrionNodeCategory, OrionNode, OrionAPMApplication, ]:
        try:
            _ret = model.update_or_create_from_orion()
        except HTTPError as error:
            _ret = str(error)
        except Exception as error:
            raise error

        ret.append(_ret)

    return ret


@shared_task(
    task_serializer='pickle',
    result_serializer='pickle', rate_limit='0.5/s', queue='orion')
def orion_entity_exists(model_name, primary_key):
    """
    this task will verify if an `Orion` entity cached by the models of
    the :ref:`Orion Integration Application` is still present on the `Orion`
    server

    :arg str model_name: the name of :class:`django.db.models.Model` model
        where the `Orion` entity is cached

    :arg int primary_key: the primary key of the `Orion` entity

    :returns: `True` or `False`; see
        :meth:`orion_integration.models.OrionBaseModel.exists_in_orion`
    :rtype: bool
    """
    return apps.get_model('orion_integration', model_name).objects.\
        get(pk=primary_key).exists_in_orion()


@shared_task(queue='orion', rate_limit='5/s')
def verify_known_orion_data():
    """
    this task is using the `Celery group primitive
    <https://docs.celeryproject.org/en/latest/userguide/canvas.html#groups>`__
    in order to launch a :func:`orion_entity_exists` task for each known `Orion`
    entity

    :returns: a list with the orion objects models and the number of objects
        for each model

    :rtype: list
    """
    ret = []
    for model in [OrionNodeCategory, OrionAPMApplication, OrionNode]:
        ids = list(model.objects.filter(
            enabled=True).all().values_list('id', flat=True))
        if not ids:
            ret.append(
                'no entries in %s. skipping...' % model._meta.verbose_name)
            continue

        group(orion_entity_exists.s(model._meta.model_name, pk) for
              pk in ids)()
        ret.append('%s: looking for %s entities' % (model._meta.verbose_name,
                                                    len(ids)))

    LOG.info('bootstrapped orion data vetting for %s:\n', ';\n'.join(ret))
