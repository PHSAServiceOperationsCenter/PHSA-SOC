"""
.. _lib:

api classes and functions for the orion_integration app

:module:    p_soc_auto.orion_integration.lib

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    aug. 14, 2018
"""
from .models import OrionNode, OrionCernerCSTNode


class OrionSslNode():
    '''
    class for orion ssl nodes
    '''
    ssl_filters = dict(orionapmapplication__application_name__icontains='ssl')

    @classmethod
    def nodes(cls, cerner_cst=True, orion_ssl=False):
        """
        :arg bool cerner_cst: use the Cerner-CST data; default: `True`

        :arg bool orion_ssl: accept orion's definition of what an SSL node is

            default: `False`

        :returns: a django queryset of orion node instances
        """
        queryset = OrionNode.objects.all()

        if cerner_cst:
            queryset = OrionCernerCSTNode.objects.all()

        if orion_ssl:
            return queryset.filter(**cls.ssl_filters).all()

        return queryset

    @classmethod
    def count(cls, cerner_cst=True, orion_ssl=False):
        """
        :returns: the number of SSL nodes
        :rtype: int
        """
        return cls.nodes(cerner_cst=cerner_cst, orion_ssl=orion_ssl).count()

    @classmethod
    def ip_addresses(cls, cerner_cst=True, orion_ssl=False):
        """
        :returns: the list of ip addresses for orion ssl nodes
        :rtype: list
        """
        return list(
            cls.nodes(cerner_cst=cerner_cst, orion_ssl=orion_ssl).
            values_list('ip_address', flat=True))
