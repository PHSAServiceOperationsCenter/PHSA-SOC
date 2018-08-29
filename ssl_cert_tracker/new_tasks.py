#!/usr/bin/env python
import logging
import xml.dom.minidom

from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from libnmap.process import NmapProcess

from ssl_cert_tracker.models import NmapCertsData, NmapHistory
from orion_integration.lib import OrionSslNode

from .db_helper import Insert_Into_CertsData

from .serializers import CertsDataSerializer

logging.basicConfig(filename='p_soc_auto.log',level=logging.DEBUG)

@shared_task
def go_node(node_id, node_address):
    """Celery worker for each orion node"""
    nmap_task = NmapProcess(node_address, options='--script ssl-cert')
    nmap_task.run()
    xml_data = nmap_task.stdout
    doc = xml.dom.minidom.parseString(xml_data)

    for host in doc.getElementsByTagName("host"):
      
        scripts = host.getElementsByTagName("script")

        record = {
            "xml_data" :xml_data, 
            "addresses" : host.getElementsByTagName("address"),
            "orion_id" : node_id,
            "common_name" : None,
            "country_name" : None,
            "organization_name" : None,
            "sig_algo" : None,
            "name" : None,
            "bits" : None,
            "md5" : None,
            "sha1" : None,
            "not_before" : None,
            "not_after" : None
        }

        for script in scripts:
            for elem in script.getElementsByTagName("elem"):           # Get cert details for each target 
                try:
                    if elem.getAttribute("key") == 'commonName':
                        if record["common_name"] is None:                           
                            record["common_name"] = elem.childNodes[0].nodeValue
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have commonName tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'organizationName':
                        if record["organization_name"] is None:
                            record["organization_name"] = elem.childNodes[0].nodeValue
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have organizationName tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'countryName':
                        if record["country_name"] is None:                           
                            record["common_name"] = elem.childNodes[0].nodeValue
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have countryName tag:%s", ex.msg)
                    
                try:
                    if elem.getAttribute("key") == 'sig_algo':
                        if record["sig_algo"] is None: 
                            record["sig_algo"] = elem.childNodes[0].nodeValue.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have sig_algo tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'name':
                        if record["name"] is None: 
                            record["name"] = elem.childNodes[0].nodeValue.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have nodeValue tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'bits':
                        if record["bits"] is None: 
                            record["bits"] = elem.childNodes[0].nodeValue.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have bits tag:%s", ex.msg)
                try:
                    if elem.getAttribute("key") == 'notBefore':
                        if record["not_before"] is None: 
                            record["not_before"] = elem.childNodes[0].nodeValue.split('T')[0]

                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have not_before tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'notAfter':
                        if record["not_after"] is None: 
                            record["not_after"] = elem.childNodes[0].nodeValue.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have not_after tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'md5':
                        if record["md5"] is None: 
                            record["md5"] = elem.childNodes[0].nodeValue.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have md5 tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'sha1':
                        if record["sha1"] is None: 
                            record["sha1"] = elem.childNodes[0].nodeValue.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have sha1 tag:%s", ex.msg)

        Insert_Into_CertsData(record)


@shared_task
def getnmapdata():
    """Celery worker to capture all nodes then it delegate each node to different worker"""
    node_obj = OrionSslNode.nodes()  
    for node in node_obj :
        try:
            go_node.delay(node.id, node.ip_address)
            logging.info("Success proceesing :%s", node.ip_address)
        except ObjectDoesNotExist as ex:
            logging.error("Error proceesing node ip message:%s" , ex.msg)

