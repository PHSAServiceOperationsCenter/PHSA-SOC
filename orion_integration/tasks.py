'''
Created on Aug 15, 2018

@author: serban
'''
import wikiquote
from celery import shared_task
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
    # TODO: this needs to becoma a chain that also deletes the models
    return OrionAPMApplication.update_or_create_from_orion()


@shared_task
def heart_beat():
    """
    return a quote from wikiquote just for grins
    """
    return wikiquote.quote_of_the_day()


@shared_task
def purge_orion_data(model):
    """
    delete all instances of a django model
    :arg model: the :class:`<django.db.models.Model>`

    :returns:

        the model verbose_name property if no instances were found for
        deletion or the number of instances that were deletes. see
        `<https://docs.djangoproject.com/en/2.1/ref/models/querysets/#delete>`_

    #TODO: replace this with `<https://trello.com/c/bDHdD6FV>`_
    """
    if model.objects.exists():
        return model.objects.all().delete()

    return 'no records found for {}'.format(model._meta.verbose_name)
