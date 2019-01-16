"""
.. _models:

django models module for the orion_flash app

:module:    p_soc_auto.orion_flash.models

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Jan. 15, 2019

"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class OrionNodeAuxAlert(models.Model):
    """
    looks like an alert, walks like and alert but talks our language
    """
    orion_node_id = models.BigIntegerField(
        _('Orion NodeId'), db_index=True, blank=False,
        help_text=_(
            'Unique Identifier for an Orion Node'))
    alert_body = models.TextField(
        _('Custom Alert Body'), blank=False, null=False)
    created_on = models.DateTimeField(
        _('created on'), db_index=True, auto_now_add=True,
        help_text=_('object creation time stamp'))
    updated_on = models.DateTimeField(
        _('updated on'), db_index=True, auto_now=True,
        help_text=_('object update time stamp'))
    enabled = models.BooleanField(
        _('enabled'), db_index=True, default=True, null=False, blank=False,
        help_text=_('if this field is disabled, the row will always be'
                    ' excluded from any active operation'))