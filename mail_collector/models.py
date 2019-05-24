"""
.. _models:

django models for the mail_collector app

:module:    mail_collector.models

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    may 24, 2019

"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from p_soc_auto_base.models import BaseModel
from citrus_borg.models import get_uuid


class MailBotLogEvents(models.Model):
    """
    model for events sent by mail monitoring bots
    """
    uuid = models.UUIDField(
        _('UUID'), unique=True, db_index=True, blank=False, null=False,
        default=get_uuid)
    source_host = models.ForeignKey(
        'citrus_borg.WinlogbeatHost', db_index=True, blank=False, null=False,
        on_delete=models.PROTECT, verbose_name=_('Event Source Host'))
    event_status = models.CharField(
        _('Status'), max_length=16, db_index=True, blank=False, null=False,
        default='TBD', help_text=_(
            'Status reported by the mail borg client for this event'))
    event_type = models.CharField(
        _('Status'), max_length=32, db_index=True, blank=False, null=False,
        default='TBD', help_text=_(
            'Status reported by the mail borg client for this event'))
    event_message = models.TextField(_('Message'), blank=True, null=True)
    event_exception = models.TextField(_('Exception'), blank=True, null=True)
    raw_message = models.TextField(_('Raw Message'), blank=True, null=True)
    is_expired = models.BooleanField(
        _('event has expired'), db_index=True, blank=False, null=False,
        default=False)
    mail_account = models.TextField(
        _('Exchange Account'), blank=True, null=True)
    mail_message = models.TextField(
        _('Exchange Message'), blank=True, null=True)
    mail_message_from = models.TextField(_('From'), blank=True, null=True)

    def __str__(self):
        return str(self.uuid)
