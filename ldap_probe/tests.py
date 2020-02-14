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
from django.utils import timezone
from hypothesis import given, assume
from hypothesis.extra.django import TestCase
from hypothesis.strategies import text, characters

from ldap_probe.models import LDAPBindCred, NonOrionADNode, OrionADNode
from orion_integration.models import OrionNode, OrionNodeCategory
from p_soc_auto_base.utils import get_or_create_user


# TODO create and delete objects before each test case instead?

# TODO should this be in some shared test library?
class UserTestCase(TestCase):
    """
    Class that provides set-up for test cases that require users
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        user = get_or_create_user()
        cls.USER_ARGS = {'created_by': user, 'updated_by': user}


class OrionTestCase(UserTestCase):
    """
    Class that provides set-up for Orion related test cases
    """
    def setUp(self):
        self.ORION_CATEGORY = OrionNodeCategory.objects.create(
            orion_id=0, **self.USER_ARGS)
        _ORION_NODE_ARGS = {
            'node_caption': 'test', 'sensor': 'test_sensor',
            'ip_address': '0.0.0.0', 'status': 'testing', 'status_orion_id': 0,
            'category': self.ORION_CATEGORY,
        }
        self.ORION_NODE_ARGS = {**_ORION_NODE_ARGS, **self.USER_ARGS}

    def tearDown(self):
        OrionNodeCategory.objects.all().delete()


class LdapBindCredTest(UserTestCase):
    """
    Tests for :class:`ldap_probe.LDAPBindCred`
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
        Test that the str representation of :class:`ldap_probe.LDAPBindCred`
        is domain\\user
        """
        LDAPBindCred.objects.create(domain=domain, username=name,
            password='password', ldap_search_base='search', **self.USER_ARGS)
        test_bind_cred = LDAPBindCred.objects.get(username=name)
        self.assertEqual(str(test_bind_cred), f'{domain}\\{name}')


class BaseAdNodeTest(OrionTestCase):
    """
    Tests for :class:`ldap_probe.BaseADNode`
    """
    def setUp(self):
        """
        Override setUpClass to set up AD nodes in test db
        """
        super().setUp()
        self.orion_node_with_dns = OrionNode.objects.create(
            node_name='withdns', orion_id=0, details_url='/dnsurl',
            node_dns='fdqn', **self.ORION_NODE_ARGS)
        self.orion_node_no_dns = OrionNode.objects.create(
            node_name='nodns', orion_id=1, details_url='/nodnsurl',
            **self.ORION_NODE_ARGS,)

        OrionADNode.objects.create(node=self.orion_node_with_dns,
                                   **self.USER_ARGS)
        OrionADNode.objects.create(node=self.orion_node_no_dns,
                                   **self.USER_ARGS)

    def tearDown(self):
        OrionADNode.objects.all().delete()
        OrionNode.objects.all().delete()
        super().tearDown()

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
    def setUp(self):
        super().setUp()
        self.orion_node = OrionNode.objects.create(
            node_name='withdns', orion_id=0, node_dns='fdqn',
            **self.ORION_NODE_ARGS)
        self.ad_node = OrionADNode.objects.create(
            node=self.orion_node, **self.USER_ARGS)

    def tearDown(self):
        OrionADNode.objects.all().delete()
        OrionNode.objects.all().delete()
        super().tearDown()

    def test_report_bad_fdqn(self):
        no_dns = OrionNode.objects.create(
            node_name='nodns', orion_id=1, **self.ORION_NODE_ARGS)
        empty_dns = OrionNode.objects.create(
            node_name='emptydns', node_dns='', orion_id=2,
            **self.ORION_NODE_ARGS)

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
        dup_orion = OrionNode.objects.create(
            node_name='dup', orion_id=1, **self.ORION_NODE_ARGS)
        self.ORION_NODE_ARGS['ip_address'] = '1.1.1.1'
        new_orion = OrionNode.objects.create(
            node_name='new', orion_id=2, **self.ORION_NODE_ARGS)

        dup_node = OrionADNode.objects.create(node=dup_orion, **self.USER_ARGS)
        new_node = OrionADNode.objects.create(node=new_orion, **self.USER_ARGS)

        ids_of_dup_nodes = OrionADNode.report_duplicate_nodes().values_list(
            'id', flat=True)

        self.assertIn(dup_node.id, ids_of_dup_nodes)
        self.assertNotIn(new_node.id, ids_of_dup_nodes)

