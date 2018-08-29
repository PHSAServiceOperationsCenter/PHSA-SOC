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
__updated__ = '2018_08_08'

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

# Create your models here.


class BaseModel(models.Model):
    """
    base class for model classes
    """
    created_by = models.ForeignKey(
        get_user_model(), on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_created_by_related',
        verbose_name=_('created by'))
    updated_by = models.ForeignKey(
        get_user_model(), on_delete=models.PROTECT,
        related_name='%(app_label)s_%(class)s_updated_by_related',
        verbose_name=_('updated by'))
    created_on = models.DateTimeField(
        _('created on'), db_index=True, auto_now_add=True,
        help_text=_('object creation time stamp'))
    updated_on = models.DateTimeField(
        _('updated on'), db_index=True, auto_now=True,
        help_text=_('object update time stamp'))
    enabled = models.BooleanField(
        _('enabled'), db_index=True, default=True, null=False, blank=False)
    notes = models.TextField(_('notes'), null=True, blank=True)

    @classmethod
    def get_or_create_user(cls, username):
        user = get_user_model().objects.filter(username__iexact=username)
        if not user.exists():
            get_user_model().objects.create_user(username)

        return user.get()

    class Meta:
        abstract = True
