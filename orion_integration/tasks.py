"""
.. _tasks:

celery tasks for the orion_integration app

:module:    p_soc_auto.orion_integration.tasks

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Sep. 5, 2018

"""
from celery import shared_task, group
from django.apps import apps
from orion_integration.models import (
    OrionAPMApplication, OrionNodeCategory, OrionNode,
)


@shared_task
def populate_from_orion():
    """
    update the models in orion_integration from the orion server

    the models are provided as an internal ``list``

    this task needs to be registered with celery and needs to be
    controlled via celery beat because currently it is not being
    invoked any where else. it is also responsible for pre-populating
    all the orion data caching models

    :returns: a list of models that were updated

    """
    ret = []
    for model in [OrionNodeCategory, OrionNode, OrionAPMApplication, ]:
        _ret = model.update_or_create_from_orion()
        ret.append(_ret)

    return ret


@shared_task(task_serializer='pickle', result_serializer='pickle')
def orion_entity_exists(model_name, primary_key):
    """
    task that answers the question "does this thing still exist in orion?"

    this task is per-instance task: for each orion integration model instance
    another instance of this task is invoked

    :arg str model_name: the name of the orion objects model
    :arg int pk: the primary key of the object

    :returns: a representation of the orion object tagged with "exists" or
              with "not seen since:"

              see
              :method:`<orion_integration.models.OrionBaseModel.exists_in_orion>`
    """
    return apps.get_model('orion_integration', model_name).objects.\
        get(pk=primary_key).exists_in_orion()


@shared_task
def verify_known_orion_data():
    """
    group task that is responsible for launching the
    :function:`<orion_entity_exists>`

    see
    `<http://docs.celeryproject.org/en/latest/userguide/canvas.html?highlight=groups#groups>`_
    for details about celery groups

    :returns: a list with the orion objects models and the number of objects
              for each model
    """
    ret = []
    for model in [OrionNodeCategory, OrionAPMApplication, OrionNode]:
        ids = list(model.objects.filter(
            enabled=True).all().values_list('id', flat=True))
        group(orion_entity_exists.s(model._meta.model_name, pk) for
              pk in ids)()
        ret.append('%s: looking for %s entities' % (model._meta.verbose_name,
                                                    len(ids)))

    return 'bootstrapped orion data vetting for %s:\n' % ';\n'.join(ret)
