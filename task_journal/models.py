"""
.. _models:

django models module for the task_journal app

:module:    p_soc_auto.task_journal.models

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

:updated:    Apr. 4, 2019

"""
from django.db import models
from django.utils.translation import gettext_lazy as _


class TaskDiaryBase(models.Model):
    """
    base model for task diary models
    """
    created_on = models.DateTimeField(
        _('created on'), db_index=True, auto_now_add=True,
        help_text=_('object creation time stamp'))
    expired = models.BooleanField(
        _('expired'), db_index=True, default=False, null=False, blank=False,
        help_text=_(
            'expired tasks will only be considered if specifically queried'))
    notes = models.TextField(_('notes'), null=True, blank=True)
    task_id = models.CharField(
        _('task ID'), max_length=64, db_index=True, unique=True, blank=False,
        null=False)
    task_name = models.CharField(
        _('task ID'), max_length=253, db_index=True, blank=False, null=False)
