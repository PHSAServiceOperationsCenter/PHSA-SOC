"""
ldap_probe.tests
----------------

This module contains tests for the :ref:`Active Directory Services Monitoring
Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from decimal import Decimal
import socket

from django.conf import settings
from django.db.models import QuerySet
from django.test import TestCase
from django.utils import timezone

from ldap_probe.models import LDAPBindCred, NonOrionADNode, OrionADNode
from orion_integration.models import OrionNode, OrionNodeCategory
from p_soc_auto_base.utils import get_or_create_user


# TODO create and delete objects before each test case instead?

# TODO should this be in some shared test library?
class UserTestCase(TestCase):
    """
    Class that provides se-tup for test cases that require users
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        USER = get_or_create_user()
        cls.USER_ARGS = {'created_by': USER, 'updated_by': USER}


class OrionTestCase(UserTestCase):
    """
    Class that provides set-up for Orion related test cases
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ORION_CATEGORY, _ = OrionNodeCategory.objects.get_or_create(
            orion_id=0, **cls.USER_ARGS)
        _ORION_NODE_ARGS = {
            'node_caption': 'test', 'sensor': 'test_sensor',
            'ip_address': '0.0.0.0', 'status': 'testing', 'status_orion_id': 0,
            'category': cls.ORION_CATEGORY,
        }
        cls.ORION_NODE_ARGS = {**_ORION_NODE_ARGS, **cls.USER_ARGS}


class LdapBindCredTest(UserTestCase):
    """
    Tests for :class:`ldap_probe.LDAPBindCred`
    """
    def setUp(self):
        LDAPBindCred.objects.create(
            domain='domain', username='user', password='password',
            ldap_search_base='search', **self.USER_ARGS)

    def test_str_is_domain_slash_user(self):
        """
        Test that the str representation of :class:`ldap_probe.LDAPBindCred`
        is domain\\user
        """
        test_bind_cred = LDAPBindCred.objects.get(username='user')
        self.assertEqual(str(test_bind_cred), 'domain\\user')


class BaseAdNodeTest(OrionTestCase):
    """
    Tests for :class:`ldap_probe.BaseADNode`
    """
    @classmethod
    def setUpClass(cls):
        """
        Override setUpClass to set up AD nodes in test db
        """
        super().setUpClass()
        cls.orion_node_with_dns, _ = OrionNode.objects.get_or_create(
            node_name='withdns', orion_id=0, details_url='/dnsurl',
            node_dns='fdqn', **cls.ORION_NODE_ARGS)
        cls.orion_node_no_dns, _ = OrionNode.objects.get_or_create(
            node_name='nodns', orion_id=1, details_url='/nodnsurl',
            **cls.ORION_NODE_ARGS,)
        # TODO should I just try create instead?
        OrionADNode.objects.get_or_create(node=cls.orion_node_with_dns,
                                          **cls.USER_ARGS)
        OrionADNode.objects.get_or_create(node=cls.orion_node_no_dns,
                                          **cls.USER_ARGS)

    def test_get_node_on_nonorionadnode_returns_node_dns(self):
        """
        Get node returns node dns when available
        """
        node, _ = NonOrionADNode.objects.get_or_create(
            node_dns='fdqn', **self.USER_ARGS)
        self.assertEqual(node.get_node(), 'fdqn')

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
    Tests for :class:`ldap_probe.OrionADNode`
    """
    @classmethod
    def setUpClass(cls):
        """
        Override setUpClass to set up AD nodes in test db
        """
        super().setUpClass()
        cls.orion_node, _ = OrionNode.objects.get_or_create(
            node_name='withdns', orion_id=0, node_dns='fdqn',
            **cls.ORION_NODE_ARGS)
        cls.ad_node, _ = OrionADNode.objects.get_or_create(
            node=cls.orion_node, **cls.USER_ARGS)

    def test_report_bad_fdqn(self):
        no_dns, _ = OrionNode.objects.get_or_create(
            node_name='nodns', orion_id=1, **self.ORION_NODE_ARGS)
        empty_dns, _ = OrionNode.objects.get_or_create(
            node_name='emptydns', node_dns='', orion_id=2,
            **self.ORION_NODE_ARGS)

        no_dns_ad, _ = OrionADNode.objects.get_or_create(
            node=no_dns, **self.USER_ARGS)
        empty_dns_ad, _ = OrionADNode.objects.get_or_create(
            node=empty_dns, **self.USER_ARGS)

        ids_of_bad_fdqns = OrionADNode.report_bad_fqdn().values_list('id',
                                                                     flat=True)

        self.assertIn(no_dns_ad.id, ids_of_bad_fdqns)
        self.assertIn(empty_dns_ad.id, ids_of_bad_fdqns)
        self.assertNotIn(self.ad_node.id, ids_of_bad_fdqns)
