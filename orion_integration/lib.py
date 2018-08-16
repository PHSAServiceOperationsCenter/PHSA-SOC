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
from .models import OrionNode


class OrionSslNode(object):
    '''
    class for orion ssl nodes
    '''
    @classmethod
    def nodes(cls):
        """
        :returns: a django queryset object with all the SSL nodes
        """
        return OrionNode.objects.\
            filter(orionapmapplication__application_name__icontains='ssl').\
            all()

    @classmethod
    def count(cls):
        """
        :returns: the number of SSL nodes
        :rtype: int
        """
        return OrionNode.objects.\
            filter(orionapmapplication__application_name__icontains='ssl').\
            count()

    @classmethod
    def ip_addresses(cls):
        """
        :returns: the list of ip addresses for orion ssl nodes
        :rtype: list
        """
        return list(
            OrionNode.objects.
            filter(orionapmapplication__application_name__icontains='ssl').
            values_list('ip_address', flat=True)
        )
