"""
.. _models:

django models for the ssl_certificates app

:module:    ssl_certificates.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""
from django.utils import timezone
from django.db import models
from p_soc_auto_base.models import BaseModel


class NmapCertsData(BaseModel, models.Model):
    """NmapCertsData. Model struture for NMap result response. """
    orion_id = models.CharField(max_length=100, blank=True, null=True)
    addresses = models.CharField(max_length=100, blank=False, null=False)
    not_before = models.DateTimeField(null=True, blank=True)
    not_after = models.DateTimeField(null=True, blank=True)
    xml_data = models.TextField()
    common_name = models.CharField(max_length=100, blank=True, null=True,
                                   help_text="A unique title for common_name")
    # TO DO
    # organizational_unit_name = models.CharField(max_length=100, blank=True, null=True,
    #                                help_text="A unique title for organizational_unit_name")
    organization_name = models.CharField(max_length=100,
                                         blank=True, null=True,
                                         help_text="A unique title for organization_name")
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
                    NmapHistory.objects.filter(orion_id=self.orion_id).update(status="found",
                                                                              retreived=timezone.now())

    def save(self, *args, **kwargs):
        super(NmapCertsData, self).save(*args, **kwargs)
        pk_val = self.pk
        self.update_cert_history(pk_val)

    def __str__(self):
        return 'O: %s, CN: %s' % (self.organization_name, self.common_name)

    @staticmethod
    def get_cert_handle(o_id):
        """get_cert_handle """
        return NmapCertsData.objects.get(orion_id=o_id)

    @staticmethod
    def get_cert_state(o_id, hash_md5):
        """orion_id_exist """
        if NmapCertsData.objects.filter(orion_id=o_id).count() == 0:
            return_code = 1  # new reord
        elif NmapCertsData.objects.filter(orion_id=o_id, md5=hash_md5).count() == 0:
            return_code = 2  # cert changed
        else:  # cert has not changed
            NmapHistory.objects.filter(orion_id=o_id,
                                       md5=hash_md5).update(
                retreived=timezone.now())
            return_code = 0
        return return_code

class NmapHistory(models.Model):
    """NmapHistory. Model struture for NMap result diff response. """
    cert_id = models.IntegerField()
    orion_id = models.CharField(max_length=100, blank=True, null=True)
    md5 = models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    retreived = models.DateTimeField(null=True, blank=True)
    xml_data = models.TextField()

    def updateRetreivedCertHist(self, md5):
        obj = NmapHistory.objects.filter(md5 = self.md5)
        obj = NmapHistory(retreived=timezone.now())
        obj.save()

    def __str__(self):
        return str(self.cert_id)


class NmapCertsScript(BaseModel, models.Model):
    """NmapCertsScript. Model struture for NMap scripts. https://nmap.org/nsedoc/"""
    name = models.CharField(max_length=100, unique=True, blank=True, null=True)
    command = models.CharField(max_length=100, blank=True, null=True)
