"""
orion_integration.lib
---------------------

This module contains the public API provided by the :ref:`Orion Integration
Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from citrus_borg.dynamic_preferences_registry import get_preference

from .models import OrionNode, OrionCernerCSTNode


class OrionSslNode():
    '''
    Class with methods for retrieving `Orion` data cached by the :ref:`Orion
    Integration Application`
    '''
    ssl_filters = dict(
        orionapmapplication__application_name__icontains=get_preference(
            'orionfilters__ssl_app'))
    """
    `Django field lookups
    <https://docs.djangoproject.com/en/2.1/ref/models/querysets/#field-lookups>`__
    that can be used by any method in this class

    """

    @classmethod
    def nodes(cls, cerner_cst=None, orion_ssl=None, servers_only=None):
        """
        get the orion nodes cached in
        :class:`orion_integration.models.OrionNode`

        :arg bool cerner_cst: only return the `Orion` nodes that have the
            `Cerner-CST` attribute set on the `Orion` server; default: `True`

        :arg bool orion_ssl: only return `Orion` nodes that are linked to an
            :class:`orion_integration.models.OrionAPMApplication` instance
            pointing to an `orion APM` node with `SSL` properties;
            default: `False`

        :arg bool servers_only: only return `Orion` nodes that are known as
            servers

        :returns: a :class:`django.db.models.query.QuerySet` based on the
            :class:`orion_integration.models.OrionNode`

        Usage example:

        .. code-block:: ipython

            In [1]: from orion_integration.lib import OrionSslNode

            In [3]: OrionSslNode.nodes().values()[0]
            Out[3]:
            {'id': 9104,
             'created_by_id': 3,
             'updated_by_id': 3,
             'created_on': datetime.datetime(2019, 6, 20, 1, 0, 41, 164415, tzinfo=<UTC>),
             'updated_on': datetime.datetime(2019, 10, 24, 13, 0, 25, 229959, tzinfo=<UTC>),
             'enabled': True,
             'notes': 'net-snmp - Linux',
             'orion_id': 6436,
             'not_seen_since': None,
             'address': '888 West 28th Avenue',
             'building': 'Ambulatory Care Building - Data Centre',
             'city': 'Vancouver',
             'closet': 'Flr: 0  RM: K0-160 - Data Center',
             'comments': None,
             'device_type': 'ACS',
             'ha': 'PHSA',
             'hardware_incident_status': None,
             'incident_status': None,
             'make': 'Cisco',
             'node_owner': 'HSSBC Security',
             'out_of_band': None,
             'program_application': 'Cerner-CST',
             'program_application_type': 'Network_ISE',
             'provider': None,
             'region': 'Vancouver',
             'site': 'Children and Womens (CW)',
             'site_contact_name': None,
             'site_hours': '24hx7d',
             'site_phone': None,
             'site_type': 'Acute-DC',
             'wan_bandwidth': None,
             'wan_node': 'False',
             'wan_provider': None,
             'node_caption': 'cw-phsa-isep01',
             'category_id': 9,
             'sensor': 'SNMP',
             'ip_address': '10.1.14.7',
             'node_name': 'Cisco Application Deployment Engine',
             'node_dns': '',
             'node_description': '',
             'vendor': 'net-snmp',
             'location': 'CW',
             'machine_type': 'net-snmp - Linux',
             'status': 'Node status is Up, eth0 is in an Unknown state.',
             'status_orion_id': 1,
             'details_url': '/Orion/NetPerfMon/NodeDetails.aspx?NetObject=N:6436'}

            In [4]:

        """
        queryset = OrionNode.objects.filter(enabled=True)

        if cerner_cst is None:
            cerner_cst = get_preference('orionprobe__cerner_cst')

        if servers_only is None:
            servers_only = get_preference('orionprobe__servers_only')

        if orion_ssl is None:
            orion_ssl = get_preference('orionprobe__orion_ssl')

        if cerner_cst:
            queryset = OrionCernerCSTNode.objects.filter(enabled=True)

        if servers_only:
            queryset = queryset.filter(
                category__category__icontains=get_preference(
                    'orionfilters__server_node'))

        if orion_ssl:
            return queryset.filter(**cls.ssl_filters).all()

        return queryset

    @classmethod
    def count(cls, cerner_cst=None, orion_ssl=None, servers_only=None):
        """
        :returns: the count of `orion` nodes for a given query
        :rtype: int

        see :meth:`nodes` for argument details
        """
        return cls.nodes(
            cerner_cst=cerner_cst,
            orion_ssl=orion_ssl, servers_only=servers_only).count()

    @classmethod
    def ip_addresses(cls, cerner_cst=None, orion_ssl=None, servers_only=None):
        """
        :returns: the list of ip addresses for the `Orion` nodes in the query
        :rtype: list

        see :meth:`nodes` for argument details
        """
        return list(
            cls.nodes(
                cerner_cst=cerner_cst,
                orion_ssl=orion_ssl, servers_only=servers_only
            ).values_list('ip_address', flat=True)
        )
