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
    return OrionAPMApplication.update_or_create_from_orion()


@shared_task(task_serializer='pickle', result_serializer='pickle')
def orion_entity_exists(instance):
    """
    does this thing still exist in orion?
    """
    return instance.exists_in_orion()


@shared_task
def vet_orion_data():
    """
    loop through orion models and instances and look if the orion objects
    are still there
    """
    for model in [OrionAPMApplication, OrionNodeCategory, OrionNode, ]:
        group(orion_entity_exists.s((instance).set(serializer='pickle')) for
              instance in model.objects.filter(enabled=True).all())()

    return 'bootstrapped orion data vetting'
