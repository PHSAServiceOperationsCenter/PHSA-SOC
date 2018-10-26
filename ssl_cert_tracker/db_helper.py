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
from ssl_cert_tracker.models import NmapCertsData

logging.basicConfig(filename='p_soc_auto.log', level=logging.DEBUG)


def insert_into_certs_data(json_data):
    """
    create or update instances of :class:`<models.NmapCertsData>`
     """

    NmapCertsData.created_by = NmapCertsData.get_or_create_user(
        username='PHSA_User')

    qs = NmapCertsData.objects.filter(md5=json_data['md5'])
    if qs.exists():
        db_certs = qs.get()
        db_certs.last_updated = timezone.now()
        db_certs.save()
        return

    db_certs = NmapCertsData()
    db_certs.node_id = json_data["node_id"]
    db_certs.addresses = json_data["addresses"]
    db_certs.created_by_id = NmapCertsData.created_by.id
    db_certs.updated_by_id = NmapCertsData.created_by.id

    db_certs.not_before = _make_aware(parse_datetime(json_data["not_before"]))

    db_certs.not_after = _make_aware(parse_datetime(json_data["not_after"]))

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

    return


def _make_aware(datetime_input, use_timezone=timezone.utc, is_dst=False):
    """
    make datetime objects to timezone aware if needed
    """
    if timezone.is_aware(datetime_input):
        return datetime_input

    return timezone.make_aware(
        datetime_input, timezone=use_timezone, is_dst=is_dst)
