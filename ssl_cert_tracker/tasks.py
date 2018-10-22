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

import xml.dom.minidom
from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from libnmap.process import NmapProcess
from orion_integration.lib import OrionSslNode

from .db_helper import insert_into_certs_data

from .utils import process_xml_cert

logging.basicConfig(filename='p_soc_auto.log', level=logging.DEBUG)


@shared_task(rate_limit='0.5/s', queue='nmap')
def go_node(node_id, node_address):
    """Celery worker for each orion node"""
    xml_data = ""
    count = 0
    while count < 5:
        count = count + 1
        try:
            nmap_task = NmapProcess(node_address, options='--script ssl-cert')
            nmap_task.run()
            xml_data = nmap_task.stdout
            break
        except Exception as ex:
            logging.error("Error proceesing xml_cert message:%s", ex)

    if count < 5:
        doc = xml.dom.minidom.parseString(xml_data)
        json = process_xml_cert(node_id, doc)
        if json["md5"] is None:
            msg = "Error Proceesing data or missing hash value"
            logging.error("Error proceesing xml_cert message:%s", msg)
        else:
            insert_into_certs_data(json)


@shared_task(queue='ssl')
def getnmapdata():
    """Celery worker to capture all nodes then it delegate each node to different worker"""
    node_obj = OrionSslNode.nodes()
    for node in node_obj:
        try:
            go_node.delay(node.id, node.ip_address)
            logging.info("Success proceesing :%s", node.ip_address)
        except ObjectDoesNotExist as ex:
            logging.error("Error proceesing node ip message:%s", ex)
