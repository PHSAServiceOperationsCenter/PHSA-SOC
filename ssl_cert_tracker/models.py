"""
.. _models:

django models for the ssl_certificates app

:module:    ssl_certificates.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""
import logging
import xml.dom.minidom
from libnmap.process import NmapProcess
from django.utils import timezone
from django.db import models
from django.utils.dateparse import parse_datetime
from p_soc_auto_base.models import BaseModel
from .utils import process_xml_cert
from .utils import validate

class NmapCertsData(BaseModel, models.Model):
    """NmapCertsData. Model struture for NMap result response. """
    orion_id = models.CharField(max_length=100, blank=True, null=True)
    addresses = models.CharField(max_length=100, blank=False, null=False)
    not_before = models.DateTimeField(null=True, blank=True)
    not_after = models.DateTimeField(null=True, blank=True)
    xml_data = models.TextField()
    common_name = models.CharField(max_length=100, blank=True, null=True,
                                   help_text="A unique title \
                                   for common_name")
    organization_name = models.CharField(max_length=100,
                                         blank=True, null=True,
                                         help_text="A unique \
                                         title for organization_name")
    country_name = models.CharField(max_length=100, blank=True, null=True)
    sig_algo = models.CharField(max_length=100, blank=True, null=True)
    name = models.CharField(max_length=100, blank=True, null=True)
    bits = models.CharField(max_length=100, blank=True, null=True)
    md5 = models.CharField(max_length=100, blank=True, null=True)
    sha1 = models.CharField(max_length=100, blank=True, null=True)

    def update_cert_history(self, pk_val=False):
        """update_cert_history. """
        if pk_val:
            orion_id_count = NmapHistory.objects.filter(
                orion_id=self.orion_id).count()
            if orion_id_count == 0:  # this is insert
                obj = NmapHistory(cert_id=int(pk_val),
                                  orion_id=self.orion_id,
                                  md5=self.md5,
                                  status="new",
                                  retreived=timezone.now(),
                                  xml_data=self.xml_data)
                obj.save()
            else:  # this is either update/insert
                md5_count = NmapHistory.objects.filter(
                    orion_id=self.orion_id, md5=self.md5).count()
                if md5_count == 0:
                    obj = NmapHistory(cert_id=int(pk_val),
                                      orion_id=self.orion_id,
                                      md5=self.md5,
                                      status="changed",
                                      retreived=timezone.now(),
                                      xml_data=self.xml_data)
                    obj.save()
                else:
                    NmapHistory.objects.filter(
                        orion_id=self.orion_id).update(
                            status="found",
                            retreived=timezone.now())

    @staticmethod
    def retreive_cert_data(node_id, node_address):
        """retreive_cert_data. """

        xml_data = ""
        try:
            nmap_task = \
            NmapProcess(node_address, options='--script ssl-cert')
            nmap_task.run()
            xml_data = nmap_task.stdout
            doc = xml.dom.minidom.parseString(xml_data)
            json = process_xml_cert(node_id, doc)
            
            if json["md5"] is not None:
                # insert_into_certs_data check if record
                # already exist then update otherwise insert
                NmapCertsData.created_by = \
                NmapCertsData.get_or_create_user(username='PHSA_User')
                cert_status = NmapCertsData.get_cert_state(json["orion_id"],
                                                           json["md5"]
                                                           )
                if cert_status not in [0, 1, 2]:
                    msg = "failure"
                    logging.error(
                        "Error accessing django model \
                        NmapCertsData get_cert_state:%s",
                        msg)
                    return

                if cert_status == 0:
                    # un-changed, update retreived column in cert hist
                    db_certs_hist = NmapHistory()
                    db_certs_hist.update_retreived_cert_hist(json["md5"])
                    msg = "un-changed, update retrieved column in cert hist!"
                    logging.info("certsHist data update:.... %s", msg)
                    return

                if cert_status == 1: #new reord
                    db_certs = NmapCertsData()
                    msg = "Unchanged!"
                    logging.info("Cert data info:.... %s", msg)

                else:
                    # cert changed cert_status == 2
                    db_certs = NmapCertsData.get_cert_handle(json["orion_id"])
                    msg = "Changed!"
                    logging.info("Cert data info:.... %s", msg)

                db_certs.orion_id = json["orion_id"]
                db_certs.addresses = json["addresses"]
                if cert_status in [1]:
                    # new record
                    db_certs.created_by_id = NmapCertsData.created_by.id
                    db_certs.updated_by_id = NmapCertsData.created_by.id
                db_certs.updated_on = timezone.now()

                if validate(json["not_before"]):
                    db_certs.not_before = parse_datetime(json["not_before"])

                if validate(json["not_after"]):
                    db_certs.not_after = parse_datetime(json["not_after"])

                db_certs.common_name = json["common_name"]
                db_certs.organization_name = json["organization_name"]
                db_certs.country_name = json["country_name"]
                db_certs.sig_algo = json["sig_algo"]
                db_certs.name = json["name"]
                db_certs.bits = json["bits"]
                db_certs.md5 = json["md5"]
                db_certs.sha1 = json["sha1"]
                db_certs.xml_data = json["xml_data"]
                db_certs.save()
        except Exception as ex:
            logging.error("Error proceesing xml_cert message:%s", ex)


    def save(self, *args, **kwargs):
        super(NmapCertsData, self).save(*args, **kwargs)
        pk_val = self.pk
        self.update_cert_history(pk_val)

    def __str__(self):
        return 'O: %s, CN: %s' % (self.organization_name,
                                  self.common_name)

    @staticmethod
    def get_cert_handle(o_id):
        """
        get_cert_handle
        """
        return NmapCertsData.objects.get(orion_id=o_id)

    @staticmethod
    def get_cert_state(o_id, hash_md5):
        """
        Check if we already have this cert in our database
        """
        if NmapCertsData.objects.filter(orion_id=o_id).count() == 0:
            return_code = 1  # new reord
        elif NmapCertsData.objects.filter(orion_id=o_id,
                                          md5=hash_md5).count() == 0:
            return_code = 2  # cert changed
        else:  # cert has not changed
            NmapHistory.objects.filter(
                orion_id=o_id, md5=hash_md5).update(retreived=timezone.now())
            return_code = 0
        return return_code

    class Meta:
        verbose_name = 'SSL Certificate Data'
        verbose_name_plural = 'SSL Certificate Data'


class NmapHistory(models.Model):
    """NmapHistory. Model struture for NMap result diff response. """
    cert_id = models.IntegerField()
    orion_id = models.CharField(max_length=100, blank=True, null=True)
    md5 = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    retreived = models.DateTimeField(null=True, blank=True)
    xml_data = models.TextField()

    def update_retreived_cert_hist(self, md5):
        """
        Updating Retreived column in Cert Hist Table
        """
        NmapHistory.objects.filter(
            md5=md5).update(retreived=timezone.now())

    def __str__(self):
        return str(self.md5)


class NmapCertsScript(BaseModel, models.Model):
    """
    NmapCertsScript
    Model struture for NMap scripts. https://nmap.org/nsedoc/
    """
    name = models.CharField(max_length=100,
                            unique=True,
                            blank=True,
                            null=True)
    command = models.CharField(max_length=100,
                               blank=True,
                               null=True)
