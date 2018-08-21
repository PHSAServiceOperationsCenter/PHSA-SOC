#!/usr/bin/env python
from random import choice
from celery import Celery
from celery import shared_task, task
from celery.decorators import periodic_task
from libnmap.process import NmapProcess
import xml.dom.minidom
import sys
import logging
import datetime
import pylint

from pocApp.models import MyCertsData
from orion_integration.lib import OrionSslNode

logger = logging.Logger('catch_all')

@shared_task
def go(node):
    rc = "Success"
    nm = NmapProcess(node, options='--script ssl-cert')
    nm.run()
    xmlData = nm.stdout
    doc = xml.dom.minidom.parseString(xmlData )

    output = []
    for host in doc.getElementsByTagName("host"):
        ip = ''
        commonName = ''
        organizationName = ''
        countryName = ''
        notBefore = ''
        notAfter = ''

        md5 = ''
        sha1 = ''
        host_name= ''
        addressip = ''
    
        addresses = host.getElementsByTagName("address")
        ip = addresses[0].getAttribute("addr")                         # Get IP address from addr element 
        scripts = host.getElementsByTagName("script")
        for script in scripts:
            for elem in script.getElementsByTagName("elem"):         # Get cert details for each target 
                try:
                    if elem.getAttribute("key") == 'commonName':
                        if commonName == '':                            # Only get the first commonName 
                            commonName =  elem.childNodes[0].nodeValue
                except:
                    pass
                try:
                    if elem.getAttribute("key") == 'organizationName':
                        if organizationName == '': 
                            organizationName =  elem.childNodes[0].nodeValue
                except:
                    pass
                try:
                    if elem.getAttribute("key") == 'countryName':
                        countryName =  elem.childNodes[0].nodeValue
                except:
                    pass
            
                try:
                    if elem.getAttribute("key") == 'notBefore':
                        notBefore =  elem.childNodes[0].nodeValue
                        notBefore = notBefore.split('T')[0]
                except:
                    pass
                try:
                    if elem.getAttribute("key") == 'notAfter':
                        notAfter =  elem.childNodes[0].nodeValue
                        notAfter = notAfter.split('T')[0]
                except:
                    pass

                try:
                    if elem.getAttribute("key") == 'md5':
                        md5 =  elem.childNodes[0].nodeValue
                        md5 =  md5.split('T')[0]
                except:
                    pass

                try:
                    if elem.getAttribute("key") == 'sha1':
                        sha1 =  elem.childNodes[0].nodeValue
                        sha1 =  sha1.split('T')[0]
                except:
                    pass

            output.append(commonName + ":" + notBefore + ',' + notAfter + ", " + host_name + ", " +  md5 + ',' + sha1)
            logger.info("output: ", output)
            print("Hello:-----------------------",output)
            try:
                dbCerts=MyCertsData()
                dbCerts.valid_start = notBefore
                dbCerts.valid_end = notAfter
                #dbCerts.xmldata = xmlData
                dbCerts.status = "new"
                dbCerts.hostname = commonName
                dbCerts.md5 = md5
                dbCerts.sha1 = sha1
                dbCerts.save()
                logger.info('nMap Record successfully uploaded')
            except Exception as e:
                logger.error('Failed to upload nMap Record: '+ str(e))
                rc = "Failed"
    return rc


@shared_task
def getnmapdata():
    rc = "success"
    try:
        nodeList = OrionSslNode.ip_addresses()
        for node in nodeList:
            rc = go.delay(node)
    except Exception as e:
        logger.error('Failed to get nMap Record: '+ str(e))
        rc = "Failed"
        
        
    return rc
