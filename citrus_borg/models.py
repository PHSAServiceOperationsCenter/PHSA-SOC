"""
.. _models:

django models for the citrus_borg app

:module:    citrus_borg.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    nov. 19, 2018

"""
import socket
import uuid

from django.conf import settings
from django.db import models
from django.db.models.deletion import SET_NULL
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from p_soc_auto_base.models import BaseModel
from orion_integration.orion import OrionClient


def get_uuid():
    """
    provide default value for UUID fields

    :returns: an instance of :class:`<uuid.UUID>` that ca  be used as a
              unique identifier
    """
    return uuid.uuid4()


class OrionNodeIDError(ValueError):
    """
    raise if we cannot grab the orion node id in :class:`<WinlogbeatHost>`
    """

# pylint: disable=too-few-public-methods,no-self-use


class BorgSiteNotSeenManager(models.Manager):
    """
    custom manager for :class:`<BorgSite>`
    """

    def get_queryset(self):
        """
        override the get_queryset method
        """
        return BorgSite.objects.\
            exclude(winlogbeathost__last_seen__gt=now() -
                    settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER)


class WinlogbeatHostNotSeenManager(models.Manager):
    """
    model manager for bot hosts not seen for a while
    """

    def get_queryset(self):
        """
        override method for custom model managers
        """
        return WinlogbeatHost.objects.\
            exclude(last_seen__gt=now() -
                    settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER)


class KnownBrokeringDeviceNotSeenManager(models.Manager):
    """
    model manager for citrix app servers

    yes, i know the class name is misleading
    """

    def get_queryset(self):
        """
        overloaded method for custom model managers
        """
        return KnownBrokeringDevice.objects.\
            exclude(last_seen__gt=now() -
                    settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER)


class CitrixHostManager(models.Manager):
    """
    get only citrix bots
    """

    def get_queryset(self):
        """
        override get_queryset to return only citrix bots
        """
        return WinlogbeatHost.objects.exclude(last_seen__isnull=True)

# pylint: enable=too-few-public-methods,no-self-use


class BorgSite(BaseModel, models.Model):
    """
    sites with with citrix bots
    """
    site = models.CharField(
        _('site name'), max_length=64, db_index=True, unique=True,
        blank=False, null=False)

    def __str__(self):
        return self.site

    class Meta:
        app_label = 'citrus_borg'
        verbose_name = _('Bot Site')
        verbose_name_plural = _('Bot Sites')


class BorgSiteNotSeen(BorgSite):
    """
    sites not seen for a while
    """
    objects = BorgSiteNotSeenManager()

    class Meta:
        proxy = True
        ordering = ('-winlogbeathost__last_seen',)
        verbose_name = _('Bot Site')
        verbose_name_plural = _('Bot Sites not seen for a while')


class WinlogbeatHost(BaseModel, models.Model):
    """
    hosts where the winlogbeat daemon is collecting windows events
    """
    host_name = models.CharField(
        _('host name'), max_length=63, db_index=True, unique=True,
        blank=False, null=False)
    ip_address = models.GenericIPAddressField(
        _('IP address'), protocol='IPv4', blank=True, null=True)
    last_seen = models.DateTimeField(
        _('Citrix bot last seen'), db_index=True, blank=True, null=True)
    excgh_last_seen = models.DateTimeField(
        _('Exchange client bot last seen'),
        db_index=True, blank=True, null=True)
    site = models.ForeignKey(
        BorgSite, db_index=True, blank=True, null=True,
        on_delete=models.SET_NULL)
    orion_id = models.BigIntegerField(
        _('Orion Object Id'), db_index=False, unique=False, blank=True,
        null=True, default=0,
        help_text=_(
            'Use the value in this field to query the Orion server'))

    @property
    def resolved_fqdn(self):
        """
        try to acquire the fqdn of the bot
        """
        return socket.getfqdn(self.ip_address) if self.ip_address else None

    def get_orion_id(self):
        """
        use the resolved_fqdn or the ip address to ask the orion server
        for the orion id

        the normal way to call this method is to wrap it a celery task
        that is part of a celery group.

        we may want to have the nodes tagged with a custom property
        application name and use that one as SWSQL key

        """
        orion_query = ('SELECT NodeID FROM Orion.Nodes(nolock=true) '
                       'WHERE ToLower(DNS)=@dns')

        if not self.enabled:
            # it's disabled, we don't care so go away
            return

        if self.resolved_fqdn is None and self.ip_address is None:
            # there is no way to identify the node in orion
            # how does orion handle unamanaged nodes? is it possible
            # to ignore network identification?

            # TODO: this is an error condition, must integrate with
            # https://trello.com/c/1Aadwukn
            return

        if self.resolved_fqdn:
            # let's use the DNS property, these nodes are mostly DHCP'ed
            orion_id = OrionClient.query(
                orion_query=orion_query,
                dns=self.resolved_fqdn)
            if orion_id:
                # but can we use the DNS property?
                self.orion_id = orion_id[0].get('NodeID', None)
                self.save()
                return

        # couldn't use DNS, falling back to IPAddress
        orion_query = ('SELECT NodeID FROM Orion.Nodes(nolock=true) '
                       'WHERE IPAddress=@ip_address')
        orion_id = OrionClient.query(
            orion_query=orion_query, ip_address=self.ip_address)

        if orion_id:
            self.orion_id = orion_id[0].get('NodeID', None)
            self.save()
            return

        raise OrionNodeIDError(
            'cannot find Citrix bot %s on the Orion server' % self.host_name)

    def __str__(self):
        return '%s (%s)' % (self.host_name, self.ip_address)

    @classmethod
    def get_or_create_from_borg(cls, borg):
        """
        get the host object based on host information in the windows event

        if the host object doesn't exist, create it first

        :arg borg: the namedtuple containing the windows event data

        :returns: a host object
        """
        last_seen = now() \
            if borg.event_source in ['ControlUp Logon Monitor'] else None
        exch_last_seen = now() \
            if borg.event_source in ['BorgExchangeMonitor'] else None

        winloghost = cls.objects.filter(
            host_name__iexact=borg.source_host.host_name)

        if winloghost.exists():
            winloghost = winloghost.get()
            winloghost.last_seen = last_seen
            winloghost.excgh_last_seen = exch_last_seen
        else:
            user = cls.get_or_create_user(settings.CITRUS_BORG_SERVICE_USER)
            winloghost = cls(
                host_name=borg.source_host.host_name, last_seen=last_seen,
                ip_address=borg.source_host.ip_address, created_by=user,
                exch_last_seen=exch_last_seen, updated_by=user)

        winloghost.save()
        return winloghost

    class Meta:
        verbose_name = _('Remote Monitoring Bot')
        verbose_name_plural = _('Remote Monitoring Bots')


class CitrixHost(WinlogbeatHost):
    """
    only citrix bots
    """
    objects = CitrixHostManager()

    class Meta:
        proxy = True
        verbose_name = _('Citrix Bot')
        verbose_name_plural = _('Citrix Bots')
        get_latest_by = '-last_seen'
        ordering = ['-last_seen', ]


class WinlogbeatHostNotSeen(WinlogbeatHost):
    """
    bots not seen for a while
    """
    objects = WinlogbeatHostNotSeenManager()

    class Meta:
        proxy = True
        verbose_name = _('Remote Monitoring Bot')
        verbose_name_plural = _('Remote Monitoring Bots not seen for a while')


class AllowedEventSource(BaseModel, models.Model):
    """
    only save events originating from specific Log_name and source_name
    combinations
    """
    source_name = models.CharField(
        _('source name'), max_length=253, db_index=True, blank=False,
        null=False, unique=True, help_text=_(
            'the equivalent of filtering by -ProviderName in Get-WinEvent:'
            ' the application will only capture events generated by'
            ' providers listed in this model'))

    def __str__(self):
        return self.source_name

    class Meta:
        verbose_name = _('Allowed Event Source')
        verbose_name_plural = _('Allowed Event Sources')


class WindowsLog(BaseModel, models.Model):
    """
    windows log names lookup
    """
    log_name = models.CharField(
        _('Log Name'), max_length=64, unique=True, db_index=True, blank=False,
        null=False)

    def __str__(self):
        return self.log_name

    class Meta:
        verbose_name = _('Supported Windows Log')
        verbose_name_plural = _('Supported Windows Logs')


class KnownBrokeringDevice(BaseModel, models.Model):
    """
    keep a list of brokers returned by the logon simulator
    """
    broker_name = models.CharField(
        _('server name'), max_length=15, unique=True, db_index=True,
        blank=False, null=False, help_text=_(
            'the name of a Citrix session server that has serviced at least'
            ' one request')
    )
    last_seen = models.DateTimeField(
        _('last seen'), db_index=True, blank=False, null=False)

    def __str__(self):
        return self.broker_name

    @classmethod
    def get_or_create_from_borg(cls, borg):
        """
        get the broker object based on host information in the windows event

        if the broker object doesn't exist, create it first

        :arg borg: the namedtuple containing the windows event data

        :returns: a host object
        """
        if borg.borg_message.broker is None:
            return None

        broker = cls.objects.filter(
            broker_name__iexact=borg.borg_message.broker)

        if broker.exists():
            broker = broker.get()
            broker.last_seen = now()
        else:
            user = cls.get_or_create_user(settings.CITRUS_BORG_SERVICE_USER)
            broker = cls(
                broker_name=borg.borg_message.broker, created_by=user,
                updated_by=user, last_seen=now())

        broker.save()
        return broker

    class Meta:
        verbose_name = _('Citrix App Server')
        verbose_name_plural = _('Citrix App Servers')


class KnownBrokeringDeviceNotSeen(KnownBrokeringDevice):
    """
    citrix app servers not seen for a while
    """
    objects = KnownBrokeringDeviceNotSeenManager()

    class Meta:
        proxy = True
        verbose_name = _('Citrix App Server')
        verbose_name_plural = _('Citrix App Servers not seen for a while')


class WinlogEvent(BaseModel, models.Model):
    """
    windows logs events
    """
    uuid = models.UUIDField(
        _('UUID'), unique=True, db_index=True, blank=False, null=False,
        default=get_uuid)
    source_host = models.ForeignKey(
        WinlogbeatHost, db_index=True, blank=False, null=False,
        on_delete=models.PROTECT,
        limit_choices_to={'last_seen__isnull': False},
        verbose_name=_('Event Source Host'))
    record_number = models.BigIntegerField(
        _('Record Number'), db_index=True, blank=False, null=False,
        help_text=_('event record external identifier'))
    event_source = models.ForeignKey(
        AllowedEventSource, db_index=True, blank=False, null=False,
        on_delete=models.PROTECT, verbose_name=_('Event Provider'))
    windows_log = models.ForeignKey(
        WindowsLog, db_index=True, blank=False, null=False,
        on_delete=models.PROTECT, verbose_name=_('Windows Log'))
    event_state = models.CharField(
        _('Status'), max_length=32, db_index=True, blank=False, null=False,
        default='TBD', help_text=_(
            'Status of the Citrix application logon request'))
    xml_broker = models.ForeignKey(
        KnownBrokeringDevice, db_index=True, blank=True, null=True,
        on_delete=SET_NULL, verbose_name=_('XML Broker'),
        help_text=_(
            'The Citrix XML Broker that successfully serviced this request'))
    event_test_result = models.NullBooleanField(_('Test Result'))
    storefront_connection_duration = models.DurationField(
        _('Storefront connection time'), db_index=True, blank=True, null=True)
    receiver_startup_duration = models.DurationField(
        _('receiver startup time'), db_index=True, blank=True, null=True)
    connection_achieved_duration = models.DurationField(
        _('Connection time'), db_index=True, blank=True, null=True)
    logon_achieved_duration = models.DurationField(
        _('Logon time'), db_index=True, blank=True, null=True)
    logoff_achieved_duration = models.DurationField(
        _('Logoff time'), db_index=True, blank=True, null=True)
    failure_reason = models.TextField(
        _('Failure Reason'), blank=True, null=True)
    failure_details = models.TextField(
        _('Failure Details'), blank=True, null=True)
    raw_message = models.TextField(
        _('Raw Message'), blank=True, null=True,
        help_text=_('the application cannot process this message'))
    is_expired = models.BooleanField(
        _('event has expired'), db_index=True, blank=False, null=False,
        default=False)

    def __str__(self):
        return str(self.uuid)

    class Meta:
        app_label = 'citrus_borg'
        verbose_name = _('Citrix Bot Windows Log Event')
        verbose_name_plural = _('Citrix Bot Windows Log Events')
        get_latest_by = '-created_on'
        ordering = ['-created_on']
