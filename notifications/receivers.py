"""
.. _apps:

django apps module for the orion integration app

:module:    p_soc_auto.notifications.apps

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

:upda
"""
from .models import Notification
from django.dispatch import receiver
from .signals import *

@receiver(Notification)
def dispatch(sender, **kwargs):
    print ("Hello I am here")
    # contains the logic to send the email to subscriber.