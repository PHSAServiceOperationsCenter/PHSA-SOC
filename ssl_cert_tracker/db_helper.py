"""
.. _models:

django models for the ssl_certificates app

:module:    db_helper.py

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""
import logging
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from ssl_cert_tracker.models import NmapCertsData, NmapHistory
from .utils import validate

logging.basicConfig(filename='p_soc_auto.log', level=logging.DEBUG)

def insert_into_certs_data(json_data):
    """insert_into_certs_data check if record already exist then update otherwise insert """

    NmapCertsData.created_by = NmapCertsData.get_or_create_user(username='PHSA_User')
    cert_status = NmapCertsData.get_cert_state(json_data["orion_id"], json_data["md5"])
    if cert_status not in [0, 1, 2]:
        msg = "failure"
        logging.error("Error accessing django model NmapCertsData get_cert_state:%s", msg)
        return
        
    if cert_status == 0: #  un-changed, update retreived column in cert hist
        db_certsHist = NmapHistory()
        db_certsHist.updateRetreivedCertHist(json_data["md5"])
        msg = "un-changed, update retrieved column in cert hist!"
        logging.info("certsHist data update:.... %s", msg)
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
    if cert_status in [1]: # new record
        db_certs.created_by_id = NmapCertsData.created_by.id
        db_certs.updated_by_id = NmapCertsData.created_by.id
    db_certs.updated_on = timezone.now()

    if validate(json_data["not_before"]):
        db_certs.not_before = parse_datetime(json_data["not_before"])

    if validate(json_data["not_after"]):
        db_certs.not_after = parse_datetime(json_data["not_after"])

    db_certs.common_name = json_data["common_name"]
    db_certs.organization_name = json_data["organization_name"]
    #db_certs.organizational_unit_name = json_data["organizational_unit_name"]
    db_certs.country_name = json_data["country_name"]
    db_certs.sig_algo = json_data["sig_algo"]
    db_certs.name = json_data["name"]
    db_certs.bits = json_data["bits"]
    db_certs.md5 = json_data["md5"]
    db_certs.sha1 = json_data["sha1"]
    db_certs.xml_data = json_data["xml_data"]
    db_certs.save()