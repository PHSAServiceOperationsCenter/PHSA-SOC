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
from celery import shared_task
from celery.utils.log import get_task_logger
from celery.exceptions import MaxRetriesExceededError
from libnmap.process import NmapProcess
from orion_integration.lib import OrionSslNode

from .db_helper import insert_into_certs_data

from .utils import process_xml_cert

logger = get_task_logger(__name__)


class NmapError(Exception):
    """
    raise on nmap failure
    """
    pass


@shared_task(
    rate_limit='0.5/s', queue='nmap', autoretry_for=(NmapError,),
    max_retries=3, retry_backoff=True)
def go_node(orion_id, node_address):
    """
    collect SSL certificate data as returned by nmap and save it to the
    database
    """
    xml_data = None
    try:
        nmap_task = NmapProcess(node_address, options='--script ssl-cert')
        nmap_task.run()
        xml_data = nmap_task.stdout
    except MaxRetriesExceededError as error:
        logger.error('')
    except Exception as ex:
        logging.error("Error proceesing xml_cert message:%s", ex)

    if count < 5:
        doc = xml.dom.minidom.parseString(xml_data)
        json = process_xml_cert(orion_id, doc)
        if json["md5"] is None:
            msg = "Error Proceesing data or missing hash value"
            logging.error("Error proceesing xml_cert message:%s", msg)
        else:
            insert_into_certs_data(json)


@shared_task(queue='ssl')
def getnmapdata():
    """
    get the orion node information that will be used for nmap probes

    #TODO: rename this to get_orion_nodes()
    #TODO: replace the go_node.delay() loop with a celery group
    """
    for node in OrionSslNode.nodes():
        try:
            go_node.delay(node.orion_id, node.ip_address)
            logging.info('queued nmap call for node %s' % node.node_caption)
        except Exception as ex:
            logging.error(
                'cannot queue nmap call for node %s: %s' % (node.node_caption,
                                                            str(ex)))
