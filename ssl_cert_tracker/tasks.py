"""
.. _models:

django models for the ssl_certificates app

:module:    new_tasks.py

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""

import logging

from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from orion_integration.lib import OrionSslNode
from .models import NmapCertsData

logging.basicConfig(filename='p_soc_auto.log', level=logging.DEBUG)

@shared_task(rate_limit='0.5/s', queue='nmap')
def go_node(node_id, node_address):
    """Serban, This method no longer needed
    If I remove it then go_node tasks still appears
    in celery worker tasks list
    """
    pass

@shared_task(queue='ssl')
def getnmapdata():
    """Celery worker to capture all nodes then
     it delegate each node to different worker
    """
    node_obj = OrionSslNode.nodes()
    for node in node_obj:
        try:
            NmapCertsData.retreive_cert_data(node.id, node.ip_address)
            logging.info("Success proceesing :%s", node.ip_address)
        except ObjectDoesNotExist as ex:
            logging.error("Error proceesing node ip message:%s", ex)
