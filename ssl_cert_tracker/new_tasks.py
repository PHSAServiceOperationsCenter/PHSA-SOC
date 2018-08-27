#!/usr/bin/env python

import logging
import xml.dom.minidom

from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from libnmap.process import NmapProcess

from ssl_cert_tracker.models import TestCertsData, TestCertsHistory
from orion_integration.lib import OrionSslNode

from .db_helper import Insert_Into_CertsData

from .serializers import MyCertsDataSerializer

logging.basicConfig(filename='pocProject.log',level=logging.DEBUG)

@shared_task
def go_node(node_id, node_address):
    """Celery worker for each orion node"""
    return_code = "Success"
    net_map = NmapProcess(node_address, options='--script ssl-cert')
    net_map.run()
    xml_data = net_map.stdout
    doc = xml.dom.minidom.parseString(xml_data )

    for host in doc.getElementsByTagName("host"):
        common_name = ''
        organization_name = ''
        country_name = ''
        not_before = ''
        not_after = ''
        md5 = ''
        sha1 = ''
        host_name = ''
        bits = ''
        name = ''
        sig_algo = ''
        record = {}
       


        addresses = host.getElementsByTagName("address")
        scripts = host.getElementsByTagName("script")
        record["xml_data"] = xml_data
        record["addresses"] = addresses
        record["orion_id"] = node_id
        record["common_name"] =""
        record["country_name"] = ""
        record["organization_name"] = ""
        record["sig_algo"] = ""
        record["name"] = ""
        record["bits"] = ""
        record["md5"] = ""
        record["sha1"] = ""

        for script in scripts:
            for elem in script.getElementsByTagName("elem"):           # Get cert details for each target 
                try:
                    if elem.getAttribute("key") == 'commonName':
                        if common_name == '':                            # Only get the first commonName 
                            record["common_name"] = elem.childNodes[0].nodeValue
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have commonName tag:%s", ex.msg)

                try:
                    record["organization_name"] = ""
                    if elem.getAttribute("key") == 'organizationName':
                        if organization_name == '': 
                            organization_name =  elem.childNodes[0].nodeValue
                            record["organization_name"] = organization_name
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have organizationName tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'countryName':
                        country_name =  elem.childNodes[0].nodeValue
                        record["country_name"] = country_name
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have countryName tag:%s", ex.msg)
                    
                try:
                    record["sig_algo"] = ""
                    if elem.getAttribute("key") == 'sig_algo':
                        sig_algo =  elem.childNodes[0].nodeValue
                        sig_algo = sig_algo.split('T')[0]
                        record["sig_algo"] = sig_algo
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have sig_algo tag:%s", ex.msg)

                try:
                    record["name"] = ""
                    if elem.getAttribute("key") == 'name':
                        name =  elem.childNodes[0].nodeValue
                        name = bits.split('T')[0]
                        record["name"] = name
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have nodeValue tag:%s", ex.msg)

                try:
                    record["bits"] = ""
                    if elem.getAttribute("key") == 'bits':
                        bits =  elem.childNodes[0].nodeValue
                        bits = bits.split('T')[0]
                        record["bits"] = bits
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have bits tag:%s", ex.msg)
                try:
                    record["not_before"] = ""
                    if elem.getAttribute("key") == 'notBefore':
                        not_before = elem.childNodes[0].nodeValue
                        not_before = not_before.split('T')[0]
                        record["not_before"] = not_before
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have not_before tag:%s", ex.msg)

                try:
                    record["not_after"] = ""
                    if elem.getAttribute("key") == 'notAfter':
                        not_after = elem.childNodes[0].nodeValue
                        not_after = not_after.split('T')[0]
                        record["not_after"] = not_after
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have not_after tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'md5':
                        md5 = elem.childNodes[0].nodeValue
                        md5 = md5.split('T')[0]
                        record["md5"] = md5
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have md5 tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'sha1':
                        sha1 = elem.childNodes[0].nodeValue
                        sha1 = sha1.split('T')[0]
                        record["sha1"] = sha1
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have sha1 tag:%s", ex.msg)

        return_code = Insert_Into_CertsData(record)

    return return_code

@shared_task
def getnmapdata():
    """Celery worker to capture all nodes then it delegate each node to different worker"""
    return_code = "Success"
    try:
        node_obj = OrionSslNode.nodes()  
        for node in node_obj :
            return_code = go_node.delay(node.id, node.ip_address)
            logging.info("Success proceesing :%s", node.ip_address)
    except ObjectDoesNotExist as ex:
        logging.error("Error proceesing node ip message:%s" , ex.msg)
        return_code = "Failed"
        
    return return_code
