"""
ldap_probe.tests
----------------

This module contains tests for the :ref:`Active Directory Services Monitoring
Application`.

:copyright:

    Copyright 2020 - Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from datetime import timedelta
from decimal import Decimal
import socket

from django.conf import settings
from django.db.models import QuerySet
from django.utils import timezone
from hypothesis import given
from hypothesis.strategies import text, characters

from ldap_probe.models import LDAPBindCred, NonOrionADNode, OrionADNode
from ldap_probe.ldap_probe_log import LdapProbeLog
from orion_integration.models import OrionNode, OrionNodeCategory
from p_soc_auto_base.test_lib import UserTestCase


class OrionTestCase(UserTestCase):
    """
    Class that provides set-up for Orion related test cases
    """
    def setUp(self):
        orion_category = OrionNodeCategory.objects.create(
            orion_id=0, **self.USER_ARGS)
        _orion_node_args = {
            'node_caption': 'test', 'sensor': 'test_sensor',
            'ip_address': '0.0.0.0', 'status': 'testing', 'status_orion_id': 0,
            'category': orion_category,
        }
        self.orion_node_args = {**_orion_node_args, **self.USER_ARGS}

    def tearDown(self):
        OrionNodeCategory.objects.all().delete()


class LdapBindCredTest(UserTestCase):
    """
    Tests for :class:`ldap_probe.models.LDAPBindCred`
    """
    @given(name=text(characters(whitelist_categories=('Lu', 'Ll', 'Nd',),
                                whitelist_characters=('_', '-',),
                                min_codepoint=0, max_codepoint=128),
                     min_size=1),
           domain=text(characters(whitelist_categories=('Lu', 'Ll', 'Nd',),
                                  whitelist_characters=('_', '-',),
                                  min_codepoint=0, max_codepoint=128),
                       min_size=1, max_size=15))
    def test_str_is_domain_slash_user(self, name, domain):
        """
        Test that the str representation of
        :class:`ldap_probe.models.LDAPBindCred` is domain\\user
        """
        LDAPBindCred.objects.create(
            domain=domain, username=name, password='password',
            ldap_search_base='search', **self.USER_ARGS)
        test_bind_cred = LDAPBindCred.objects.get(username=name)
        self.assertEqual(str(test_bind_cred), f'{domain}\\{name}')


class BaseAdNodeTest(OrionTestCase):
    """
    Tests for :class:`ldap_probe.models.BaseADNode`
    """
    def setUp(self):
        """
        Override setUp to set up AD nodes in test db
        """
        super().setUp()
        self.orion_node_with_dns = OrionNode.objects.create(
            node_name='withdns', orion_id=0, details_url='/dnsurl',
            node_dns='fdqn', **self.orion_node_args)
        self.orion_node_no_dns = OrionNode.objects.create(
            node_name='nodns', orion_id=1, details_url='/nodnsurl',
            **self.orion_node_args,)

        OrionADNode.objects.create(node=self.orion_node_with_dns,
                                   **self.USER_ARGS)
        OrionADNode.objects.create(node=self.orion_node_no_dns,
                                   **self.USER_ARGS)

    def tearDown(self):
        OrionADNode.objects.all().delete()
        OrionNode.objects.all().delete()
        super().tearDown()

    # TODO fix this test (create non orion node then delete)
    def test_get_node_on_nonorionadnode_returns_node_dns(self):
        """
        Get node returns node dns when available
        """
        node = NonOrionADNode.objects.create(node_dns='fdqn', **self.USER_ARGS)
        self.assertEqual(node.get_node(), 'fdqn')
        node.delete()

    def test_get_node_with_orionnode_with_dns_returns_orion_dns(self):
        """
        Get node returns dns from orion node when available
        """
        node = OrionADNode.objects.get(node=self.orion_node_with_dns)
        self.assertEqual(node.get_node(), 'fdqn')

    def test_get_node_with_orionnode_without_dns_returns_orion_ip(self):
        """
        Get node returns ip address from orion node when it doesn't have dns
        """
        node = OrionADNode.objects.get(node=self.orion_node_no_dns)
        self.assertEqual(node.get_node(), '0.0.0.0')

    def test_annotate_orion_url_nonorionadnodes(self):
        """
        annotate_orion_url adds 'not defined in orion' message for non orion
        AD nodes
        """
        annotated = NonOrionADNode.annotate_orion_url()
        for node in annotated:
            self.assertEqual(
                node['orion_url'],
                f'AD node {node["node_dns"]} is not defined in Orion')

    def test_annotate_orion_url_orionadnodes_with_dns(self):
        """
        Orion url points to 'orion.vch.ca'
        """
        annotated = OrionADNode.annotate_orion_url()\
            .get(node=self.orion_node_with_dns)
        self.assertEqual(annotated['orion_url'], 'https://orion.vch.ca/dnsurl')

    # TODO is this test case necessary?
    def test_annotate_orion_url_orionadnodes_no_dns(self):
        """
        Orion url works even if dns is not defined
        """
        annotated = OrionADNode.annotate_orion_url()\
            .get(node=self.orion_node_no_dns)
        self.assertEqual(annotated['orion_url'],
                         'https://orion.vch.ca/nodnsurl')

    # TODO verify that the page gives the right data
    def test_annotate_probe_details_nonorionadnode_anon_bind(self):
        """
        Probe details url is as expected for anonymous probes on non-orion ad
        nodes
        """
        annotated_list = NonOrionADNode.annotate_probe_details(
            'ldapprobeanonbindlog').all()
        for annotated in annotated_list:
            self.assertIn(f'{settings.SERVER_PROTO}://{socket.getfqdn()}:'
                          f'{settings.SERVER_PORT}/admin/ldap_probe/'
                          f'ldapprobeanonbindlog/?ad_node__id=',
                          annotated['probes_url'])

    def test_annotate_probe_details_nonorionadnode_full_bind(self):
        """
        Probe details url is as expected for full probes on non-orion ad nodes
        """
        annotated_list = NonOrionADNode.annotate_probe_details(
            'ldapprobefullbindlog').all()
        for annotated in annotated_list:
            self.assertIn(f'{settings.SERVER_PROTO}://{socket.getfqdn()}:'
                          f'{settings.SERVER_PORT}/admin/ldap_probe/'
                          f'ldapprobefullbindlog/?ad_node__id=',
                          annotated['probes_url'])

    def test_annotate_probe_details_orionadnode_anon_bind(self):
        """
        Probe details url is as expected for anonymous probes on orion ad nodes
        """
        annotated_list = OrionADNode.annotate_probe_details(
            'ldapprobeanonbindlog').all()
        for annotated in annotated_list:
            self.assertIn(f'{settings.SERVER_PROTO}://{socket.getfqdn()}:'
                          f'{settings.SERVER_PORT}/admin/ldap_probe/'
                          f'ldapprobeanonbindlog/?ad_orion_node__id=',
                          annotated['probes_url'])

    def test_annotate_probe_details_orionadnode_full_bind(self):
        """
        Probe details url is as expected for full probes on orion ad nodes
        """
        annotated_list = OrionADNode.annotate_probe_details(
            'ldapprobefullbindlog').all()
        for annotated in annotated_list:
            self.assertIn(f'{settings.SERVER_PROTO}://{socket.getfqdn()}:'
                          f'{settings.SERVER_PORT}/admin/ldap_probe/'
                          f'ldapprobefullbindlog/?ad_orion_node__id=',
                          annotated['probes_url'])

    # TODO unclear on what are the proper tests
    def test_report_perf_report_perf_degradation(self):
        """
        Report perf degradation returns expected elements
        """
        now, time_delta, subscription, queryset, threshold, no_nodes\
            = OrionADNode.report_perf_degradation()
        self.assertIsInstance(now, timezone.datetime)
        self.assertIsInstance(time_delta, timezone.timedelta)
        self.assertIsInstance(subscription, str)
        self.assertIsInstance(queryset, QuerySet)
        self.assertIsInstance(threshold, Decimal)
        self.assertIsInstance(no_nodes, bool)

    def test_report_probe_aggregates(self):
        """
        Report perf probe aggregates returns expected elements
        """
        now, time_delta, subscription, queryset, threshold\
            = OrionADNode.report_probe_aggregates()
        self.assertIsInstance(now, timezone.datetime)
        self.assertIsInstance(time_delta, timezone.timedelta)
        self.assertIsInstance(subscription, str)
        self.assertIsInstance(queryset, QuerySet)
        self.assertIsInstance(threshold, int)


class OrionAdNodeTest(OrionTestCase):
    """
    Tests for :class:`ldap_probe.models.OrionADNode`
    """
    def setUp(self):
        super().setUp()
        self.orion_node = OrionNode.objects.create(
            node_name='withdns', orion_id=0, node_dns='fdqn',
            **self.orion_node_args)
        self.ad_node = OrionADNode.objects.create(
            node=self.orion_node, **self.USER_ARGS)

    def tearDown(self):
        OrionADNode.objects.all().delete()
        OrionNode.objects.all().delete()
        super().tearDown()

    def test_report_bad_fdqn(self):
        """
        Test that report_bad_fdqn returns orion nodes that have either empty
        dns or no dns, but not nodes that have any value in their dns field
        """
        no_dns = OrionNode.objects.create(
            node_name='nodns', orion_id=1, **self.orion_node_args)
        empty_dns = OrionNode.objects.create(
            node_name='emptydns', node_dns='', orion_id=2,
            **self.orion_node_args)

        no_dns_ad = OrionADNode.objects.create(
            node=no_dns, **self.USER_ARGS)
        empty_dns_ad = OrionADNode.objects.create(
            node=empty_dns, **self.USER_ARGS)

        ids_of_bad_fdqns = OrionADNode.report_bad_fqdn().values_list('id',
                                                                     flat=True)

        self.assertIn(no_dns_ad.id, ids_of_bad_fdqns)
        self.assertIn(empty_dns_ad.id, ids_of_bad_fdqns)
        self.assertNotIn(self.ad_node.id, ids_of_bad_fdqns)

    def test_report_duplicate_nodes(self):
        """
        Test that report_duplicate_nodes returns nodes that have the same ip
        address
        """
        dup_orion = OrionNode.objects.create(
            node_name='dup', orion_id=1, **self.orion_node_args)
        self.orion_node_args['ip_address'] = '1.1.1.1'
        new_orion = OrionNode.objects.create(
            node_name='new', orion_id=2, **self.orion_node_args)

        dup_node = OrionADNode.objects.create(node=dup_orion, **self.USER_ARGS)
        new_node = OrionADNode.objects.create(node=new_orion, **self.USER_ARGS)

        ids_of_dup_nodes = OrionADNode.report_duplicate_nodes().values_list(
            'id', flat=True)

        self.assertIn(dup_node.id, ids_of_dup_nodes)
        self.assertNotIn(new_node.id, ids_of_dup_nodes)


class NonOrionAdNodeTest(UserTestCase):
    """
    Tests for :class:`ldap_probe.models.OrionADNode`
    """
    def setUp(self):
        super().setUp()
        self.node = NonOrionADNode.objects.create(**self.USER_ARGS)

    def tearDown(self):
        NonOrionADNode.objects.all().delete()
        super().tearDown()

    # TODO test remove_if_in_orion somehow


class LdapProbeLogTest(UserTestCase):
    """
    Tests for :class:`ldap_probe.models.LdapProbeLog`
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.test_delta = timedelta(hours=10)
        cls.node = NonOrionADNode.objects.create(**cls.USER_ARGS)

    @classmethod
    def tearDownClass(cls):
        LdapProbeLog.objects.all().delete()
        NonOrionADNode.objects.all().delete()
        super().tearDownClass()

    def test_error_report_does_not_include_old_logs(self):
        """
        test old logs are not included in error report
        """
        log = LdapProbeLog.objects.create(ad_node=self.node, created=0)
        self.assertNotIn(log, LdapProbeLog.error_report(self.test_delta))

    def test_error_report_includes_failed_logs(self):
        """
        test error report includes failed logs
        """
        log = LdapProbeLog.objects.create(ad_node=self.node, failed=True)
        self.assertIn(log, LdapProbeLog.error_report(self.test_delta))

    def test_error_report_does_not_include_pass(self):
        """
        test error report does not include successes
        """
        log = LdapProbeLog.objects.create(ad_node=self.node)
        self.assertNotIn(log, LdapProbeLog.error_report(self.test_delta))

    def test_create_from_probe(self):
        """
        test create from probe creates an ldap probe log entry
        """
        probe_data = {
            'elapsed_initialize': 1,
            'elapsed_bind': 1,
            'elapsed_search_ext': 1,
            'ad_controller': self.node,
            'ad_response': 'Probe Response',
            'errors': '',
            'failed': False,
        }
        LdapProbeLog.create_from_probe(probe_data)
        self.assertTrue(
            LdapProbeLog.objects.filter(ad_response='Probe Response'))
