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

from citrus_borg.models import get_uuid, WinlogbeatHost, BorgSite


class MailHostManager(models.Manager):  # pylint: disable=too-few-public-methods
    """
    only show bots with exchange monitoring clients
    """

    def get_queryset(self):  # pylint: disable=no-self-use
        """
        override get_queryset
        """
        return WinlogbeatHost.objects.exclude(excgh_last_seen__isnull=True)


class MailSiteManager(models.Manager):  # pylint: disable=too-few-public-methods
    """
    only the sites that have exchange monitoring clients
    """

    def get_queryset(self):  # pylint: disable=no-self-use
        """
        override get_queryset
        """
        return BorgSite.objects.filter(
            winlogbeathost__excgh_last_seen__isnull=False).distinct()


class MailSite(BorgSite):
    """
    model for exchnage client sites
    """
    objects = MailSiteManager()

    class Meta:
        proxy = True
        verbose_name = _('Exchange Monitoring Site')
        verbose_name_plural = _('Exchange Monitoring Sites')
        get_latest_by = '-winlogbeathost__excgh_last_seen'
        ordering = ['-winlogbeathost__excgh_last_seen', ]


class MailHost(WinlogbeatHost):
    """
    proxy model for exchange client bots
    """
    objects = MailHostManager()

    class Meta:
        proxy = True
        verbose_name = _('Exchange Monitoring Bot')
        verbose_name_plural = _('Exchange Monitoring Bots')
        get_latest_by = '-excgh_last_seen'
        ordering = ['-excgh_last_seen', ]


class MailBotLogEvent(models.Model):
    """
    model for events sent by mail monitoring bots
    """
    event_group_id = models.CharField(
        _('Session Id'), max_length=128, db_index=True, blank=False,
        null=False,
        help_text=_(
            'Identifier for a group of related exchange client events'))
    uuid = models.UUIDField(
        _('UUID'), unique=True, db_index=True, blank=False, null=False,
        default=get_uuid)
    source_host = models.ForeignKey(
        'citrus_borg.WinlogbeatHost', db_index=True, blank=False, null=False,
        on_delete=models.PROTECT,
        limit_choices_to={'excgh_last_seen__isnull': False},
        verbose_name=_('Event Source Host'))
    event_status = models.CharField(
        _('Status'), max_length=16, db_index=True, blank=False, null=False,
        default='TBD', help_text=_(
            'Status reported by the mail borg client for this event'))
    event_type = models.CharField(
        _('Type'), max_length=32, db_index=True, blank=False, null=False,
        default='TBD', help_text=_('Type of this event'))
    event_type_sort = models.IntegerField(
        _('Sort Value for Type'), db_index=True, blank=False, null=False,
        default=999,
        help_text=(
            'connect (1) before sent (2) before received (3) and so on'))
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
        return '%s: %s' % (str(self.uuid), self.event_message)

    class Meta:
        app_label = 'mail_collector'
        verbose_name = _('Mail Monitoring Event')
        verbose_name_plural = _('Mail Monitoring Events')
        ordering = ['-event_group_id', 'mail_account', 'event_type_sort']
        get_latest_by = '-event_registered_on'


class MailBotMessage(models.Model):
    """
    model for mail monitoring messages
    """
    mail_message_identifier = models.CharField(
        _('Exchange Message Identifier'), max_length=36, db_index=True,
        blank=False, null=False)
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
        return '%s: %s' % (str(self.event.uuid), self.event.event_message)

    class Meta:
        app_label = 'mail_collector'
        verbose_name = _('Mail Monitoring Message')
        verbose_name_plural = _('Mail Monitoring Messages')
        ordering = ['-event__event_group_id',
                    'sent_from', 'event__event_type_sort', ]
        get_latest_by = '-event__event_registered_on'


class ExchangeServer(models.Model):
    """
    the exchange servers being monitored
    """
    exchange_server = models.CharField(
        _('Exchange Server'), max_length=16, db_index=True, unique=True,
        blank=False, null=False)
    last_connection = models.DateTimeField(
        _('Last Connected'), db_index=True, blank=True, null=True,
        help_text=_(
            'Last time an account connected successfully to this server'))
    last_send = models.DateTimeField(
        _('Last Send'), db_index=True, blank=True, null=True,
        help_text=_('Last time a message was send via this server'))
    last_inbox_access = models.DateTimeField(
        _('Last Inbox Access'), db_index=True, blank=True, null=True,
        help_text=_('Can also be considered as last received'))
    last_updated = models.DateTimeField(
        _('Last Updated'), db_index=True, blank=False, null=False,
        auto_now=True)
    enabled = models.BooleanField(
        _('Enabled'), db_index=True, blank=False, null=False, default=True)
    last_updated_from_node_id = models.BigIntegerField(
        _('Orion Node Id'), db_index=True, blank=False, null=False,
        default=0,
        help_text=_('this is the value in this field to'
                    ' SQL join the Orion server database'))

    def __str__(self):
        return self.exchange_server

    class Meta:
        app_label = 'mail_collector'
        verbose_name = _('Exchange Server')
        verbose_name_plural = _('Exchange Servers')
        ordering = ['-last_updated']
        get_latest_by = '-last_updated'


class ExchangeDatabase(models.Model):
    """
    exchange database instances
    """
    database = models.CharField(
        _('Database'), max_length=16, db_index=True, unique=True, blank=False,
        null=False)
    exchange_server = models.ForeignKey(
        ExchangeServer, db_index=True, blank=False, null=False,
        on_delete=models.CASCADE, verbose_name=_('Exchange Server'))
    last_access = models.DateTimeField(
        _('Last Access'), db_index=True, blank=False, null=False)
    enabled = models.BooleanField(
        _('Enabled'), db_index=True, blank=False, null=False, default=True)
    last_updated_from_node_id = models.BigIntegerField(
        _('Orion Node Id'), db_index=True, blank=False, null=False,
        default=0,
        help_text=_('this is the value in this field to'
                    ' SQL join the Orion server database'))

    def __str__(self):
        return self.database

    class Meta:
        app_label = 'mail_collector'
        verbose_name = _('Exchange Database')
        verbose_name_plural = _('Exchange Databases')
        ordering = ['-last_access']
        get_latest_by = '-last_access'


class MailBetweenDomains(models.Model):
    """
    track user side email functionality between specific email domains for each
    site
    """
    from_domain = models.CharField(
        _('Sent from email domain'), max_length=63, db_index=True, blank=False,
        null=False)
    to_domain = models.CharField(
        _('Received by email domain'), max_length=63, db_index=True,
        blank=False, null=False)
    site = models.ForeignKey(
        MailSite, db_index=True, null=True, blank=True,
        on_delete=models.SET_NULL, verbose_name=_('Verified from mail site'))
    is_expired = models.BooleanField(
        _('event has expired'), db_index=True, blank=False, null=False,
        default=False)
    enabled = models.BooleanField(
        _('Enabled'), db_index=True, blank=False, null=False, default=True)
    last_verified = models.DateTimeField(
        _('Last Verified'), db_index=True, blank=False, null=False)
    status = models.CharField(
        _('Status'), max_length=16, db_index=True, blank=False, null=False,
        default='TBD')
    last_updated_from_node_id = models.BigIntegerField(
        _('Orion Node Id'), db_index=True, blank=False, null=False,
        default=0,
        help_text=_('this is the value in this field to'
                    ' SQL join the Orion server database'))

    def __str__(self):
        return '{}: from {} to {}'.format(
            self.site.site, self.from_domain, self.to_domain)

    class Meta:
        app_label = 'mail_collector'
        verbose_name = _('Domain to Domain Mail Verification')
        verbose_name_plural = _('Domain to Domain Mail Verifications')
        indexes = [
            models.Index(fields=['site', 'from_domain', 'to_domain'],
                         name='mailbetweendomains_idx'),
        ]
        unique_together = ['site', 'from_domain', 'to_domain']
        ordering = [
            #'site',
            'from_domain', 'to_domain', '-last_verified']
        get_latest_by = '-last_verified'
