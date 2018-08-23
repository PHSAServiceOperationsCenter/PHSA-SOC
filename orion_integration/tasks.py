'''
Created on Aug 15, 2018

@author: serban
'''
import wikiquote
from celery import shared_task
from orion_integration.models import OrionAPMApplication


@shared_task
def populate_from_orion():
    """
    update the models in orion_integration from the orion server

    the method invoked will take care of intermediate models like OrionNode
    this may need to change to a more maintainable code
    """
    return OrionAPMApplication.update_or_create_from_orion()


@shared_task
def heart_beat():
    return wikiquote.quote_of_the_day()
