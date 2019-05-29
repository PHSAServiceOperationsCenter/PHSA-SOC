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
from django.db import models
from django.utils.translation import gettext_lazy as _

from p_soc_auto_base.models import BaseModel
from citrus_borg.models import get_uuid


class MailBotLogEvent(models.Model):
    """
    model for events sent by mail monitoring bots
    """
    uuid = models.UUIDField(
        _('UUID'), unique=True, db_index=True, blank=False, null=False,
        default=get_uuid)
    source_host = models.ForeignKey(
        'citrus_borg.WinlogbeatHost', db_index=True, blank=False, null=False,
        on_delete=models.PROTECT,
        limit_choices_to={'exch_last_seen__isnull': False},
        verbose_name=_('Event Source Host'))
    event_status = models.CharField(
        _('Status'), max_length=16, db_index=True, blank=False, null=False,
        default='TBD', help_text=_(
            'Status reported by the mail borg client for this event'))
    event_type = models.CharField(
        _('Type'), max_length=32, db_index=True, blank=False, null=False,
        default='TBD', help_text=_('Type of this event'))
    event_message = models.TextField(_('Message'), blank=True, null=True)
    event_exception = models.TextField(_('Exception'), blank=True, null=True)
    event_body = models.TextField(
        _('Raw Data'), blank=True, null=True,
        help_text=_('The full event information as collected from the wire'))
    is_expired = models.BooleanField(
        _('event has expired'), db_index=True, blank=False, null=False,
        default=False)
    mail_account = models.TextField(
        _('Exchange Account Associated With This Event'), blank=True,
        null=True,
        help_text=_('Usually DOMAIN\\user, the primaty email address'))
    event_registered_on = models.DateTimeField(
        _('Event Registered on'), db_index=True, auto_now_add=True,
        help_text=_('Database date/time stamp for the registration of'
                    ' this event to the application'))

    def __str__(self):
        return str(self.uuid)

    class Meta:
        app_label = 'mail_collector'
        verbose_name = _('Mail Monitoring Event')
        verbose_name_plural = _('Mail Monitoring Events')


class MailBotMessage(models.Model):
    """
    model for mail monitoring messages
    """
    mail_message_identifier = models.CharField(
        _('Exchange Message Identifier'), max_length=36, db_index=True,
        unique=True, blank=False, null=False)
    sent_from = models.TextField(_('Sent From'), blank=True, null=True)
    sent_to = models.TextField(_('Sent To'), blank=True, null=True)
    received_from = models.TextField(_('Received From'), blank=True, null=True)
    received_by = models.TextField(_('Received By'), blank=True, null=True)
    mail_message_created = models.DateTimeField(
        _('Created'), db_index=True, blank=True, null=True)
    mail_message_sent = models.DateTimeField(
        _('Sent'), db_index=True, blank=True, null=True)
    mail_message_received = models.DateTimeField(
        _('Received'), db_index=True, blank=True, null=True)
    event = models.OneToOneField(
        MailBotLogEvent, primary_key=True, on_delete=models.CASCADE)

    def __str__(self):
        return 'message %s from %s to %s' % (self.mail_message_identifier,
                                             self.sent_from,
                                             self.sent_to)

    class Meta:
        app_label = 'mail_collector'
        verbose_name = _('Mail Monitoring Message')
        verbose_name_plural = _('Mail Monitoring Messages')
