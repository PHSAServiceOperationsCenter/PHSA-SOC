#!/usr/bin/env python

from datetime import datetime
import time
import logging

from django.core.exceptions import ObjectDoesNotExist
from ssl_cert_tracker.models import NmapCertsData, NmapHistory
from django.conf import settings

from .utils import *

logging.basicConfig(filename='p_soc_auto.log', level=logging.DEBUG)

def Insert_Into_CertsData(json_data): 
    """Insert_Into_CertsData check if record already exist then update otherwise insert """
    try:
        NmapCertsData.created_by=NmapCertsData.get_or_create_user(username='PHSA_User')
        cert_status = NmapCertsData.get_cert_state(json_data["orion_id"], json_data["md5"])
        if cert_status not in [0, 1, 2]:
            msg = "failure"
            logging.error("Error accessing django model NmapCertsData get_cert_state:%s", msg)
            return
        elif cert_status == 0: #  cert has not changed
            msg = "To be decided!"
            logging.info("Cert data update:.... %s", msg)
            return
        elif cert_status == 1:# new reord
            db_certs = NmapCertsData()
            msg = "Unchanged!"
            logging.info("Cert data info:.... %s", msg)
        else: # cert changed cert_status == 2
            db_certs = NmapCertsData.get_cert_handle(json_data["orion_id"])
            msg = "Changed!"
            logging.info("Cert data info:.... %s", msg)

        db_certs.orion_id = json_data["orion_id"]
        db_certs.addresses = json_data["addresses"]
        
        db_certs.created_by_id= NmapCertsData.created_by.id
        db_certs.updated_by_id= NmapCertsData.created_by.id
        
        db_certs.updated_on = datetime.now().strftime ("%Y-%m-%d %H:%M:%S.%f")
               
        if validate(json_data["not_before"]):
            not_after_posix = time.mktime(datetime.strptime(json_data["not_before"], \
            "%Y-%m-%d").timetuple())
            db_certs.not_before = datetime.utcfromtimestamp(not_after_posix).isoformat() + 'Z'
        
        if validate(json_data["not_after"]):
            not_after_posix = time.mktime(datetime.strptime(json_data["not_after"], "%Y-%m-%d").timetuple())
            db_certs.not_after = datetime.utcfromtimestamp(not_after_posix).isoformat() + 'Z'

        db_certs.common_name = json_data["common_name"]
        db_certs.organization_name = json_data["organization_name"]
        db_certs.country_name = json_data["country_name"]
        db_certs.sig_algo = json_data["sig_algo"]
        db_certs.name = json_data["name"] 
        db_certs.bits = json_data["bits"]
        db_certs.md5 = json_data["md5"]
        db_certs.sha1 = json_data["sha1"]
        db_certs.xml_data = json_data["xml_data"]
        db_certs.save()
        logging.info("Success updating model TestCertsData")
    except ObjectDoesNotExist as ex:
        logging.error("Error accessing django model NmapCertsData :%s", ex.msg)

def process_date_field(date_text):
    """check if date_text is a valid date  """
    try:
        if date_text != datetime.strptime(date_text, "%Y-%m-%d").strftime('%Y-%m-%d'):
            raise ValueError
        return True
    except ValueError:
        return False