"""
.. _models:

django models for the base app

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

base models
===========

base models classes
"""
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class BaseModel(models.Model):
    """
    base class for model classes
    """
    created_on = models.DateTimeField(
        _('created on'), db_index=True, auto_now_add=True,
        help_text=_('object creation time stamp'))
    updated_on = models.DateTimeField(
        _('updated on'), db_index=True, auto_now_add=True,
        help_text=_('object update time stamp'))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        name=_('created by'))
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        name=_('updated by'))
    enabled = models.BooleanField(
        _('enabled'), db_index=True, default=True, null=False, blank=False)
    notes = models.TextField(_('notes'), db_index=True, null=True, blank=True)

    class Meta:
        abstract = True
