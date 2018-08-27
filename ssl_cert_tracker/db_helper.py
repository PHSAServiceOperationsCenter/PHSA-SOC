#!/usr/bin/env python

from datetime import datetime
import time
import logging

from django.db.models.signals import post_save

from django.core.signals import request_finished
from django.dispatch import receiver

from django.core.exceptions import ObjectDoesNotExist
from ssl_cert_tracker.models import TestCertsData, TestCertsHistory

logging.basicConfig(filename='pocProject.log',level=logging.DEBUG)

def Insert_Into_CertsData(json_data):
    """Insert_Into_CertsData """
    return_code = "Success"
    try:
        db_certs = TestCertsData()
        db_certs.orion_id = json_data["orion_id"]
        db_certs.addresses = json_data["addresses"]
        
        if "not_before" in json_data and validate(json_data["not_before"]) == True:
            not_after_posix = time.mktime(datetime.datetime.strptime(json_data["not_before"], "%Y-%m-%d").timetuple())
            db_certs.not_before = datetime.utcfromtimestamp(not_after_posix).isoformat() + 'Z'
        
        if "not_after" in json_data and validate(json_data["not_after"]) == True:
            not_after_posix = time.mktime(datetime.datetime.strptime(json_data["not_after"], "%Y-%m-%d").timetuple())
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
        logging.error("Error accessing django model TestCertsData :%s", ex.msg)
        return_code = "Failed"
    
    return return_code

def validate(date_text):
    try:
        if date_text != datetime.strptime(date_text, "%Y-%m-%d").strftime('%Y-%m-%d'):
            raise ValueError
        return True
    except ValueError:
        return False