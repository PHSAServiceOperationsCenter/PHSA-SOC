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

    the method invoked will take care of intermediate models
    like OrionNode

    this may need to change to a more maintainable code
    """
    for model in [OrionNodeCategory, OrionNode, OrionAPMApplication, ]:
        return model.update_or_create_from_orion()


@shared_task(task_serializer='pickle', result_serializer='pickle')
def orion_entity_exists(model_name, pk):
    """
    does this thing still exist in orion?

    :arg str model_name: the name of the orion objects model
    :arg int pk: the primary key of the object

    :returns: a representation of the orion object tagged with "exists" or
              with "not seen since:"
    """
    return apps.get_model('orion_integration', model_name).objects.\
        get(pk=pk).exists_in_orion()


@shared_task
def verify_known_orion_data():
    """
    check that existing orion objects data still matches what the Orion
    server thinks

    :returns: a list with the orion objects models and the number of objects
              fro each model
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
