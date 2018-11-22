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
import uuid

from django.conf import settings
from django.db import models
from django.utils.timezone import timedelta
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords

from p_soc_auto_base.models import BaseModel
from django.db.models.deletion import SET_NULL


def get_uuid():
    """
    provide default value for UUID fields

    :returns: an instance of :class:`<uuid.UUID>` that ca  be used as a
              unique identifier
    """
    return uuid.uuid4()


class WinlogbeatHost(BaseModel, models.Model):
    """
    hosts where the winlogbeat daemon is collecting windows events
    """
    host_name = models.CharField(
        _('host name'), max_length=63, db_index=True, unique=True,
        blank=False, null=False)
    ip_address = models.GenericIPAddressField(
        _('IP address'), protocol='IPv4', blank=True, null=True)
    history = HistoricalRecords()

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
        winloghost = cls.objects.filter(
            host_name__iexact=borg.source_host.hostname)

        if winloghost.exist():
            return winloghost.get()

        user = cls.get_or_create_user(settings.CITRUS_BORG_SERVICE_USER)
        winloghost = cls(
            host_name=borg.source_host.hostname,
            ip_address=borg.source_host.ip_address, created_by=user,
            updated_by=user)
        winloghost.save()
        return winloghost

    class Meta:
        verbose_name = _('Citrix Bot')
        verbose_name_plural = _('Citrix Bots')


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
    history = HistoricalRecords()

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
        _('broker name'), max_length=15, unique=True, db_index=True,
        blank=False, null=False, help_text=_(
            'the name of a CST broker that has serviced at least one request')
    )
    history = HistoricalRecords()

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

        if broker.exist():
            return broker.get()

        user = cls.get_or_create_user(settings.CITRUS_BORG_SERVICE_USER)
        broker = cls(
            broker_name=borg.borg_message.broker, created_by=user,
            updated_by=user)
        broker.save()
        return broker

    class Meta:
        verbose_name = _('Citrix XML Broker')
        verbose_name_plural = _('Citrix XML Brokers')


class WinlogEvent(BaseModel, models.Model):
    """
    windows logs events
    """
    uuid = models.UUIDField(
        _('UUID'), unique=True, db_index=True, blank=False, null=False,
        default=get_uuid)
    source_host = models.ForeignKey(
        WinlogbeatHost, db_index=True, blank=False, null=False,
        on_delete=models.PROTECT, verbose_name=_('Event Source Host'))
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
    is_expired = models.BooleanField(
        _('event has expired'), db_index=True, blank=False, null=False,
        default=False)

    def __str__(self):
        return self.uuid
