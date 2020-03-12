"""
citrus_borg.tests
-----------------

This module contains tests for the :ref:`Citrus Borg Application`.

:copyright:

    Copyright 2020 - Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
import collections

from django.conf import settings
from django.utils import timezone

from citrus_borg.models import WinlogbeatHost, BorgSite, BorgSiteNotSeen, \
    CitrixHost, KnownBrokeringDevice, EventCluster, WinlogEvent, \
    AllowedEventSource, WindowsLog
from p_soc_auto_base.test_lib import UserTestCase


# TODO this is pretty ugly...
def _empty_borg():
    borg = collections.namedtuple('Borg',
                                  ['source_host', 'record_number', 'opcode',
                                   'level', 'event_source', 'windows_log',
                                   'borg_message', 'mail_borg_message',
                                   'event_id', 'timestamp'])

    borg_host = collections.namedtuple('BorgHost',
                                       ['host_name', 'ip_address', ])

    borg_host.host_name = 'Test'
    borg_host.ip_address = '1.1.1.1'

    borg_message = collections.namedtuple('BorgMessage',
        ['state', 'broker', 'test_result', 'storefront_connection_duration',
            'receiver_startup_duration', 'connection_achieved_duration',
            'logon_achieved_duration', 'logoff_achieved_duration',
            'failure_reason', 'failure_details', 'raw_message'])

    borg_message.raw_message = 'a message was not provided with this event'
    borg_message.state = 'undetermined'
    borg_message.broker = 'TestBroker'
    borg_message.test_result = False
    borg_message.storefront_connection_duration = None
    borg_message.receiver_startup_duration = None
    borg_message.connection_achieved_duration = None
    borg_message.logon_achieved_duration = None
    borg_message.logoff_achieved_duration = None
    borg_message.failure_reason = None
    borg_message.failure_details = None

    borg.source_host = borg_host
    borg.record_number = 0
    borg.opcode = None
    borg.level = None
    borg.event_source = None
    borg.windows_log = None
    borg.event_id = None
    borg.timestamp = None
    borg.borg_message = borg_message
    borg.mail_borg_message = None

    return borg


class BorgSiteNotSeenTest(UserTestCase):
    """
    Tests for :class:`citrus_borg.models.BorgSiteNotSeen`
    """
    def setUp(self):
        WinlogbeatHost.objects.all().delete()
        BorgSite.objects.all().delete()
        self.borgsite = BorgSite.objects.create(site='Site', **self.USER_ARGS)
        self.winlogbeathost = WinlogbeatHost.objects.create(
            host_name='Name', ip_address='1.1.1.1',
            last_seen=timezone.now(), site=self.borgsite, orion_id=0,
            **self.USER_ARGS
        )

    def tearDown(self):
        WinlogbeatHost.objects.all().delete()
        BorgSite.objects.all().delete()

    def test_borgsitenotseen_doesnotincludeactiveborgsite(self):
        """
        test that recently seen sites are not in the BorgSiteNotSeen queryset
        """
        self.assertEqual(len(BorgSiteNotSeen.objects.all()), 0)

    def test_borgsitenotseen_includesforgottenborgsite(self):
        """
        test that BorgSiteNotSeen queryset includes sites that have not been
        seen recently
        """
        self.winlogbeathost.last_seen = (
            timezone.now()
            - settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER
            - settings.CITRUS_BORG_NOT_FORGOTTEN_UNTIL_AFTER
        )
        self.winlogbeathost.save()
        self.assertNotEqual(len(BorgSiteNotSeen.objects.all()), 0)


class WinlogbeatHostTest(UserTestCase):
    """
    Tests for :class:`citrus_borg.models.WinlogbeatHost`
    """
    def setUp(self):
        self.winlogbeathost = WinlogbeatHost.objects.create(
            host_name='TestHostName', **self.USER_ARGS
        )

    def teardown(self):
        self.winlogbeathost.delete()

    def test_orionnodeurlfornonorionhost_returnsstr(self):
        """
        Test that orion node url returns the expected default when none is
        supplied
        """
        self.assertEqual(self.winlogbeathost.orion_node_url,
                         'acquired outside the Orion infrastructure')
    # TODO should probably test the orion case as well.

    def test_resolvedfqdnlocalhost_resolvescorrectly(self):
        """
        test that resolved fqdn returns localhost when supplied with 127.0.0.1
        """
        self.winlogbeathost.ip_address = '127.0.0.1'
        self.winlogbeathost.save()
        self.assertEqual(self.winlogbeathost.resolved_fqdn,
                         'localhost.localdomain')

    def test_resolvedfqdnmissingip_returnsnone(self):
        self.assertEqual(self.winlogbeathost.resolved_fqdn, None)

    # TODO test get_orion_id

    # TODO could be hypothesisized
    def test_getorcreatefromborg(self):
        """
        tes that get or create from borg creates a winlogbeat host
        """
        winloghost = WinlogbeatHost.get_or_create_from_borg(_empty_borg())
        self.assertNotEqual(winloghost, None)

        winloghost.delete()


class CitrixHostTest(UserTestCase):
    """
    Tests for :class:`citrus_borg.models.CitrixHost`
    """
    def setUp(self):
        WinlogbeatHost.objects.all().delete()

    def tearDown(self):
        WinlogbeatHost.objects.all().delete()

    def test_haventseen_isexcluded(self):
        """
        test that hosts that have a null `last_seen` aren't included in the
        CitrixHost queryset
        """
        WinlogbeatHost.objects.create(
            host_name='TestHostName', **self.USER_ARGS
        )

        self.assertEqual(len(CitrixHost.objects.all()), 0)

    def test_hasseen_incollection(self):
        """
        test that the CitrixHost queryset includes hosts that have been seen
        recently (ie now-ish)
        """
        winlogbeathost = WinlogbeatHost.objects.create(
            host_name='TestHostName', last_seen=timezone.now(), **self.USER_ARGS
        )

        self.assertIn(winlogbeathost, CitrixHost.objects.all())


class KnownBrokeringDeviceTest(UserTestCase):
    """
    Tests for :class:`citrus_borg.models.KnownBrokeringDevice`
    """
    def test_getorcreatefromborg(self):
        """
        test that get or create from borg creates a known brokering devcie entry
        """
        kbd = KnownBrokeringDevice.get_or_create_from_borg(_empty_borg())
        self.assertNotEqual(kbd, None)
        kbd.delete()


#TODO test all NotSeen proxy classes?


class EventClusterTest(UserTestCase):
    """
    Tests for :class:`citrus_borg.models.EventCluster`
    """
    def setUp(self):
        host = WinlogbeatHost.objects.first()
        source = AllowedEventSource.objects.first()
        log = WindowsLog.objects.first()

        self.times = []
        for i in range(5):
            self.times.append(timezone.now())
            WinlogEvent.objects.create(
                source_host=host, record_number=0, event_source=source,
                windows_log=log, timestamp=self.times[i], **self.USER_ARGS)

        self.cluster = EventCluster.objects.create(**self.USER_ARGS)
        self.cluster.winlogevent_set.add(*list(WinlogEvent.objects.all()))

    def tearDown(self):
        EventCluster.objects.all().delete()
        WinlogEvent.objects.all().delete()

    def test_starttime_firsttime(self):
        """
        test that start time is the earliest time recoded in the cluster
        """
        self.assertEqual(self.cluster.start_time, self.times[0])

    def test_endtime_lasttime(self):
        """
        test that end time is the latest time recorded in the cluster
        """
        self.assertEqual(self.cluster.end_time, self.times[-1])

