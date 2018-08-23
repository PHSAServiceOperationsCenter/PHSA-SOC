#!/usr/bin/env python

import logging
import xml.dom.minidom

from django.core.exceptions import ObjectDoesNotExist
from celery import shared_task
from libnmap.process import NmapProcess

from pocApp.models import TestCertsData
from orion_integration.lib import OrionSslNode

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
        ip_value = ''
        md5 = ''
        sha1 = ''
        host_name = ''
        bits = ''
        name = ''
        sig_algo = ''
    
        addresses = host.getElementsByTagName("address")
        ip_value = addresses[0].getAttribute("addr")                   # Get IP address from addr element 
        scripts = host.getElementsByTagName("script")
        for script in scripts:
            for elem in script.getElementsByTagName("elem"):           # Get cert details for each target 
                try:
                    if elem.getAttribute("key") == 'commonName':
                        if common_name == '':                            # Only get the first commonName 
                            common_name =  elem.childNodes[0].nodeValue
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have commonName tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'organizationName':
                        if organization_name == '': 
                            organization_name =  elem.childNodes[0].nodeValue
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have organizationName tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'countryName':
                        country_name =  elem.childNodes[0].nodeValue
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have countryName tag:%s", ex.msg)
                
                try:
                    if elem.getAttribute("key") == 'sig_algo':
                        sig_algo =  elem.childNodes[0].nodeValue
                        sig_algo = sig_algo.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have sig_algo tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'name':
                        name =  elem.childNodes[0].nodeValue
                        name = bits.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have nodeValue tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'bits':
                        bits =  elem.childNodes[0].nodeValue
                        bits = bits.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have bits tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'notBefore':
                        not_before = elem.childNodes[0].nodeValue
                        not_before = not_before.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have not_before tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'notAfter':
                        not_after = elem.childNodes[0].nodeValue
                        not_after = not_after.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have not_after tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'md5':
                        md5 = elem.childNodes[0].nodeValue
                        md5 = md5.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have md5 tag:%s", ex.msg)

                try:
                    if elem.getAttribute("key") == 'sha1':
                        sha1 = elem.childNodes[0].nodeValue
                        sha1 = sha1.split('T')[0]
                except xml.parsers.expat.ExpatError as ex:
                    logging.info("nMap Record does not have sha1 tag:%s", ex.msg)
            try:
                db_certs = TestCertsData()
                db_certs.ip_value = ip_value
                db_certs.valid_start = not_before
                db_certs.valid_end = not_after
                #dbCerts.xmldata = xmlData
                db_certs.status = "new"
                db_certs.organizationName = organization_name
                db_certs.countryName = country_name
                db_certs.commonName = common_name
                db_certs.sig_algo = sig_algo
                db_certs.name = name
                db_certs.bits = bits
                db_certs.hostname = host_name
                db_certs.md5 = md5
                db_certs.sha1 = sha1
                db_certs.orion_id = node_id
                db_certs.save()
                logging.info("Success updating model TestCertsData")
            except ObjectDoesNotExist as ex:
                logging.error("Error accessing django model TestCertsData :%s", ex.msg)
                return_code = "Failed"
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
