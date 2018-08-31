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
    def nodes(cls, cerner_cst=True):
        """
        :returns: a django queryset object with all the SSL nodes
        """
        if cerner_cst:
            return OrionCernerCSTNode.objects.filter(**cls.ssl_filters).all()

        return OrionNode.objects.filter(**cls.ssl_filters).all()

    @classmethod
    def count(cls, cerner_cst=True):
        """
        :returns: the number of SSL nodes
        :rtype: int
        """
        return cls.nodes(cerner_cst=cerner_cst).count()

    @classmethod
    def ip_addresses(cls, cerner_cst=True):
        """
        :returns: the list of ip addresses for orion ssl nodes
        :rtype: list
        """
        return list(
            cls.nodes(cerner_cst=cerner_cst).values_list('ip_address',
                                                         flat=True))
