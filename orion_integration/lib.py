"""
.. _lib:

api classes and functions for the orion_integration app

the classes and methods from this module constitute the formal, public, and
published API provided by this application

:module:    p_soc_auto.orion_integration.lib

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    aug. 14, 2018
"""
from .models import OrionNode, OrionCernerCSTNode


class OrionSslNode():
    # pylint:disable=C0301

    '''
    class with methods for retrieving orion nodes information from models
    defined in this application

    :classvar ssl_filters:

            django field lookups available for all the methods defined in
            this class

            see
            `Field lookups<https://docs.djangoproject.com/en/2.1/ref/models/querysets/#field-lookups>`_
            for details
    '''
    # pylint:enable=C0301

    ssl_filters = dict(orionapmapplication__application_name__icontains='ssl')

    @classmethod
    def nodes(cls, cerner_cst=True, orion_ssl=False, servers_only=True):
        # pylint:disable=C0301
        """
        get the orion nodes cached in
        :model:`orion_integration.models.OrionNode`

        :arg bool cerner_cst: only return the Orion nodes that have the
                              Cerner-CST attribute set on the Orion server

                              default: `True`

        :arg bool orion_ssl: only return Orion nodes that are linked to an
                             OrionAPMApplication object defined as being an
                             SSL application

                             default: `False`

        :arg bool servers_only: only return orion nodes that are known servers

        :returns: a django queryset of orion node instances

        get all the nodes that are known Cerner-CST nodes example::

            .. code-block:: python

            from orion_integrattion.lib import OrionSslNode

            def get_nodes():
                return list(OrionSslNode.nodes().values(
                    'orion_nodeid', 'node_name', 'ip_address', 'site'))


        this will return a `list` of `dict` where each `dict` looks like::

            {'orion_id': 54,
             'node_name': 'HP Comware Platform Software, Software Version 7.1.045, Release 2416\r\nHP 5900AF-48XG-4QSFP+ Switch\r\nCopyright (c) 2010-2014 Hewlett-Packard Development Company, L.P.',
             'ip_address': '10.26.101.11',
             'site': 'Squamish General Hospital'}

        """
        # pylint:enable=C0301

        queryset = OrionNode.objects.filter(enabled=True)

        if cerner_cst:
            queryset = OrionCernerCSTNode.objects.filter(enabled=True)

        if servers_only:
            queryset = queryset.filter(category__category__icontains='server')

        if orion_ssl:
            return queryset.filter(**cls.ssl_filters).all()

        return queryset

    @classmethod
    def count(cls, cerner_cst=True, orion_ssl=False, servers_only=True):
        """
        :returns: the number of SSL nodes
        :rtype: int

        see :method:`<nodes>` for argument details
        """
        return cls.nodes(
            cerner_cst=cerner_cst,
            orion_ssl=orion_ssl, servers_only=servers_only).count()

    @classmethod
    def ip_addresses(cls, cerner_cst=True, orion_ssl=False, servers_only=True):
        """
        :returns: the list of ip addresses for orion ssl nodes
        :rtype: list

        see :method:`<nodes>` for argument details
        """
        return list(
            cls.nodes(
                cerner_cst=cerner_cst,
                orion_ssl=orion_ssl, servers_only=servers_only
            ).values_list('ip_address', flat=True)
        )
