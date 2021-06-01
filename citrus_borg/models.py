"""
.. _citrus_models

citrus_borg.models
------------------

This module contains the :class:`models <django.db.models.Model>` and
:class:`model managers <django.db.models.Manager>` used by the
:ref:`Citrus Borg Application`.

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

"""
import socket
from logging import getLogger

from django.conf import settings
from django.db import models
from django.db.models import Max, Min
from django.db.models.deletion import SET_NULL
from django.utils.safestring import mark_safe
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _

from p_soc_auto_base.preferences import get_preference
from orion_integration.models import OrionNode
from orion_integration.orion import OrionClient
from p_soc_auto_base.models import BaseModel
from p_soc_auto_base.utils import get_or_create_user, get_uuid


LOG = getLogger(__name__)


class OrionNodeIDError(ValueError):
    """
    Custom :exc:`ValueError` class raised if we cannot retrieve the orion node
    id of a host described by a :class:`WinlogbeatHost` instance
    """

# pylint: disable=too-few-public-methods,no-self-use


class NotSeenManager(models.Manager):
    """
    `Custom manager
    <https://docs.djangoproject.com/en/2.2/topics/db/managers/"""\
        """#custom-managers>`__
    class used in the 'NotSeen' models
    """

    def get_queryset(self):
        """
        override :meth:`django.db.models.Manager.get_queryset`

        See `Modifying a manager's initial QuerySet
        <https://docs.djangoproject.com/en/2.2/topics/db/managers/"""\
            """#modifying-a-manager-s-initial-queryset>`__
        in the `Django` docs.

        :returns: a :class:`django.db.models.query.QuerySet` with the
            instances that have not sent any events for the period defined by
            :attr:`p_soc_auto.settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER`

        .. todo::

            Extend
            :attr:`p_soc_auto.settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER`
            with a dynamic preference.

        """
        try:
            exclude_str = self.model.last_seen_str
        except AttributeError:
            exclude_str = 'last_seen__gt'
        return super().get_queryset().\
            exclude(**{exclude_str:
                       now() - settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER})


class CitrixHostManager(models.Manager):
    """
    `Custom manager
    <https://docs.djangoproject.com/en/2.2/topics/db/managers/"""\
        """#custom-managers>`__
    class used in the :class:`CitrixHost` model
    """

    def get_queryset(self):
        """
        override :meth:`django.db.models.Manager.get_queryset`

        See `Modifying a manager's initial QuerySet
        <https://docs.djangoproject.com/en/2.2/topics/db/managers/"""\
            """#modifying-a-manager-s-initial-queryset>`__
        in the `Django` docs.

        :returns: a :class:`django.db.models.query.QuerySet` with the
            :class:`CitrixHost` instances that have not sent any events for the
            period defined by
            :attr:`p_soc_auto.settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER`

        .. todo::

            Replace
            :attr:`p_soc_auto.settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER`
            with a dynamic preference.

        """
        return super().get_queryset().exclude(last_seen__isnull=True)

# pylint: enable=too-few-public-methods,no-self-use


class BorgSite(BaseModel, models.Model):
    """
    :class:`django.db.models.Model` class used for storing information about the
    remote sites where various data collection bots are hosted

    `Bot Site fields
    <../../../admin/doc/models/citrus_borg.borgsite>`__
    """
    site = models.CharField(
        _('site name'), max_length=64, db_index=True, unique=True,
        blank=False, null=False)

    last_seen_str = 'winlogbeathost__last_seen__gt'

    def __str__(self):
        return self.site

    class Meta:
        app_label = 'citrus_borg'
        verbose_name = _('Bot Site')
        verbose_name_plural = _('Bot Sites')


class BorgSiteNotSeen(BorgSite):
    """
    `Proxy model
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models>`__
    for :class:`BorgSite`

    See :class:`NotSeenManager`.
    """
    objects = NotSeenManager()

    class Meta:
        proxy = True
        ordering = ('-winlogbeathost__last_seen',)
        verbose_name = _('Bot Site')
        verbose_name_plural = _('Bot Sites not seen for a while')


class WinlogbeatHost(BaseModel, models.Model):
    """
    :class:`django.db.models.Model` class used for storing information about the
    remote hosts where various data collection bots are running

    Data in this `model` is maintained primarily by background processes.

    `Remote Monitoring Bot fields
    <../../../admin/doc/models/citrus_borg.winlogbeathost>`__
    """
    host_name = models.CharField(
        _('host name'), max_length=63, db_index=True, unique=True,
        blank=False, null=False)
    ip_address = models.GenericIPAddressField(
        _('IP address'), protocol='IPv4', blank=True, null=True)
    last_seen = models.DateTimeField(
        _('Citrix bot last seen'), db_index=True, blank=True, null=True)
    exchange_last_seen = models.DateTimeField(
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
    exchange_client_config = models.ForeignKey(
        'mail_collector.ExchangeConfiguration',
        blank=True, null=True, on_delete=models.SET_NULL,
        db_index=True, verbose_name=_('Exchange client configuration'))

    @property
    @mark_safe
    def orion_node_url(self):
        """
        :returns: an instance property with the `URL` of the
            `Django Admin change` form for the
            :class:`orion_integration.models.OrionNode` instance representing
            the host

        """
        orion_node = OrionNode.objects.filter(orion_id=self.orion_id)
        if orion_node.exists():
            orion_node = orion_node.values('node_caption', 'details_url')[0]
            return '<a href="%s%s">%s on Orion</>' % (
                get_preference('orionserverconn__orion_server_url'),
                orion_node.get('details_url'), orion_node.get('node_caption')
            )

        return 'acquired outside the Orion infrastructure'

    @property
    def resolved_fqdn(self):
        """
        :returns: an instance property with the `FQDN
            <https://en.wikipedia.org/wiki/Fully_qualified_domain_name>`__ of
            the host if it can be resolved or `None`

        """
        return socket.getfqdn(self.ip_address) if self.ip_address else None

    def get_orion_id(self):
        """
        get the `SolarWinds Orion
        <https://www.solarwinds.com/solutions/orion>`__ server unique identifier
        for the network node and save it to the :attr:`WinlogbeatHost.orion_id`
        field

        Because this method accesses data over the network, the proper way to
        call it is to wrap it in a `Celery task
        <https://docs.celeryproject.org/en/latest/userguide/tasks.html>`__.
        Within the :ref:`Citrus Borg Application` this method is called from the
        :func:`citrus_borg.tasks.get_orion_id` task.

        The method depends on the instance having a valid `IP address` that
        resolves to the host `FQDN
        <https://en.wikipedia.org/wiki/Fully_qualified_domain_name>`__ known to
        the `SolarWinds Orion <https://www.solarwinds.com/solutions/orion>`__
        server.

        The method will not query the `SolarWinds Orion
        <https://www.solarwinds.com/solutions/orion>`__ server if the instance
        is `disabled`.

        :returns: the instance `host_name` for the retrieved `Orion` `NodeId`,
            or an information message if the node cannot be found on the
            `Orion` server, or `None` if the :attr:`WinlogbeatHost.ip_address`
            field is null

        """
        orion_query = ('SELECT NodeID FROM Orion.Nodes(nolock=true) '
                       'WHERE ToLower(DNS)=@dns')

        if not self.enabled or (self.resolved_fqdn is None
                                and self.ip_address is None):
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
            LOG.info('updated Orion NodeID for %s', self.host_name)

        LOG.warning('cannot find bot %s on the Orion server', self.host_name)

    def __str__(self):
        return '%s (%s)' % (self.host_name, self.ip_address)

    @classmethod
    def get_or_create_from_borg(cls, borg):
        """
        maintain the host information based on data in the `Windows` log event

        If a :class:`WinlogbeatHost` instance matching the information in the
        `borg` argument doesn't exist, one will be created.

        This `class method
        <https://docs.python.org/3.6/library/functions.html?highlight=classmethod#classmethod>`__
        is invoked from the :func:`citrus_borg.tasks.store_borg_data` task.

        :arg borg: a :func:`collections.namedtuple` with the processed `Windows`
            log event data

            See the functions in the :mod:`citrus_borg.locutus.assimilation`
            module for the structure of the :func:`namedtuple
            <collections.namedtuple>`.

        :returns: the :class:`WinlogbeatHost` instance
        """

        if borg.event_source == 'ControlUp Logon Monitor':
            last_seen = now()
        else:
            last_seen = None

        if borg.event_source == 'BorgExchangeMonitor':
            exch_last_seen = now()
        else:
            exch_last_seen = None

        winloghost = cls.objects.filter(
            host_name__iexact=borg.source_host.host_name)

        if winloghost.exists():
            winloghost = winloghost.get()
            if last_seen:
                winloghost.last_seen = last_seen
            if exch_last_seen:
                winloghost.exchange_last_seen = exch_last_seen
        else:
            user = get_or_create_user(settings.CITRUS_BORG_SERVICE_USER)
            winloghost = cls(
                host_name=borg.source_host.host_name, last_seen=last_seen,
                ip_address=borg.source_host.ip_address, created_by=user,
                exchange_last_seen=exch_last_seen, updated_by=user)

        winloghost.save()
        return winloghost

    class Meta:
        app_label = 'citrus_borg'
        verbose_name = _('Remote Monitoring Bot')
        verbose_name_plural = _('Remote Monitoring Bots')


class CitrixHost(WinlogbeatHost):
    """
    `Proxy model
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models>`__
    for :class:`WinlogbeatHost` that will show only hosts where a `ControlUp`
    bot is running

    See :class:`CitrixHostManager`.
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
    `Proxy model
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models>`__
    for :class:`WinlogbeatHost`

    See :class:`NotSeenManager`.
    """
    objects = NotSeenManager()

    class Meta:
        proxy = True
        verbose_name = _('Remote Monitoring Bot')
        verbose_name_plural = _('Remote Monitoring Bots not seen for a while')


class AllowedEventSource(BaseModel, models.Model):
    """
    :class:`django.db.models.Model` class used for storing information about the
    `Windows` log event `Application` property

    Only events with a matching value for the `Application` property will be
    processed.

    `Allowed Event Source fields
    <../../../admin/doc/models/citrus_borg.allowedeventsource>`__
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
    :class:`django.db.models.Model` class used for storing information about the
    `Windows` log

    Only events from `Windows` logs with names matching entries in this model
    will be processed.

    `Supported Windows Log fields
    <../../../admin/doc/models/citrus_borg.windowslog>`__
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
    :class:`django.db.models.Model` class used for storing information about the
    `Citrix` application servers

    This model is maintained by background processes.

    `Known Brokering Device fields
    <../../../admin/doc/models/citrus_borg.knownbrokeringdevice>`__
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
        maintain the `Citrix` application servers information based on data in
        the `Windows` log event

        If a :class:`KnownBrokeringDevice` instance matching the information in
        the `borg` argument doesn't exist, one will be created.

        This `class method
        <https://docs.python.org/3.6/library/functions.html#classmethod>`__
        is invoked from the :func:`citrus_borg.tasks.store_borg_data` task.

        :arg borg: a :func:`collections.namedtuple` with the processed `Windows`
            log event data

            See the functions in the :mod:`citrus_borg.locutus.assimilation`
            module for the structure of the :func:`namedtuple
            <collections.namedtuple>`.

        :returns: the :class:`KnownBrokeringDevice` instance
        """
        if borg.borg_message.broker is None:
            return None

        broker = cls.objects.filter(
            broker_name__iexact=borg.borg_message.broker)

        if broker.exists():
            broker = broker.get()
            broker.last_seen = now()
        else:
            user = get_or_create_user(settings.CITRUS_BORG_SERVICE_USER)
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
    `Proxy model
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models>`__
    for :class:`KnownBrokeringDeviceNotSeen`

    See :class:`NotSeenManager`.
    """
    objects = NotSeenManager()

    class Meta:
        proxy = True
        verbose_name = _('Citrix App Server')
        verbose_name_plural = _('Citrix App Servers not seen for a while')


class EventCluster(BaseModel, models.Model):
    """
    :class:`django.db.models.Model` class used for storing cluster of `Citrix`
    events. The many-to-one relationship is maintained by foreign keys in the
    :class:`WinlogEvent` model.
    """
    uuid = models.UUIDField(
        _('UUID'), unique=True, db_index=True, blank=False, null=False,
        default=get_uuid)

    @property
    def start_time(self):
        """
        Earliest time of an event in the cluster

        :return: The timestamp of the first event in the cluster
        """
        return self.winlogevent_set.all().aggregate(
            Min('timestamp'))['timestamp__min']

    @property
    def end_time(self):
        """
        Latest time of an event in the cluster

        :return: The timestamp of the last event in the cluster
        """
        return self.winlogevent_set.all().aggregate(
            Max('timestamp'))['timestamp__max']

    class Meta:
        app_label = 'citrus_borg'
        verbose_name = _('Cluster of Citrix Logon Failures')
        verbose_name_plural = _('Clusters of Citrix Logon Failures')


class WinlogEvent(BaseModel, models.Model):
    """
    :class:`django.db.models.Model` class used for storing `Citrix`  events

    The data stored in this model is maintained entirely via background
    processes.

    `Citrix Bot Windows Log Event fields
    <../../../admin/doc/models/citrus_borg.winlogEvent>`__
    """
    csv_fields = [
        'uuid', 'source_host__host_name', 'source_host__site__site',
        'record_number', 'event_state', 'storefront_connection_duration',
        'receiver_startup_duration', 'connection_achieved_duration',
        'logon_achieved_duration', 'logoff_achieved_duration', 'created']
    """
    use these fields when exporting the data in this model to csv
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
    event_id = models.BigIntegerField(
        _('Event ID'), db_index=True, blank=True, null=True,
        help_text=_('the type of the event represented by this log')
    )
    timestamp = models.DateTimeField(
        _('Timestamp'), db_index=True, blank=True, null=True,
        help_text=_('windows log event creation time stamp'))
    raw_message = models.TextField(
        _('Raw Message'), blank=True, null=True,
        help_text=_('the application cannot process this message'))
    is_expired = models.BooleanField(
        _('event has expired'), db_index=True, blank=False, null=False,
        default=False)
    cluster = models.ForeignKey(
        EventCluster, on_delete=SET_NULL, blank=True, null=True,
        verbose_name=_('Alert Cluster'),
        help_text=_('The cluster this event belongs to. May be null.'))

    def __str__(self):
        return str(self.uuid)

    class Meta:
        app_label = 'citrus_borg'
        verbose_name = _('Citrix Bot Windows Log Event')
        verbose_name_plural = _('Citrix Bot Windows Log Events')
        get_latest_by = 'created'
        ordering = ['-created']
