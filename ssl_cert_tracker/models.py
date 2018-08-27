"""
.. _models:

django models for the ssl_certificates app

:module:    ssl_certificates.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""
from django.db import models
from django.db.models import signals
from django.dispatch import receiver

class TestCertsData(models.Model):
    """TestCertsData. Model struture for NMap result response. """
    orion_id =  models.CharField(max_length=100, blank=True, null=True)
    addresses =  models.CharField(max_length=100, blank=True, null=True)
    not_before = models.DateTimeField(null=True, blank=True)
    not_after = models.DateTimeField(null=True, blank=True)
    xml_data = models.TextField()
    common_name =  models.CharField(max_length=100, blank=True, null=True)
    organization_name =  models.CharField(max_length=100, blank=True, null=True)
    country_name =  models.CharField(max_length=100, blank=True, null=True)
    sig_algo =  models.CharField(max_length=100, blank=True, null=True)
    name =  models.CharField(max_length=100, blank=True, null=True)
    bits =  models.CharField(max_length=100, blank=True, null=True)
    md5 =  models.CharField(max_length=100, blank=True, null=True)
    sha1 =  models.CharField(max_length=100, blank=True, null=True)
    
    xml_data =  models.TextField(blank=True, null=True)

    def update_cert_history(self, pk_val=False):
        if pk_val:
            orion_id_count = TestCertsHistory.objects.filter(orion_id = self.orion_id).count()
            print(orion_id_count)
            if orion_id_count == 0:
                print ("We are doing insert....")
                obj = TestCertsHistory(cert_id = int(pk_val), orion_id=self.orion_id, md5=self.md5, status="new",xml_data=self.xml_data )
                obj.save()
            else: # this is either update/insert
                md5_count = TestCertsHistory.objects.filter(orion_id=self.orion_id).filter(md5=self.md5).count()
                if md5_count == 0:
                    print ("We are doing insert....")
                    obj = TestCertsHistory(cert_id=int(pk_val), \
                                           orion_id=self.orion_id, \
                                           md5=self.md5, \
                                           status="changed", \
                                           xml_data=self.xml_data)
                    obj.save()
                else:
                    print ("Certificate found.....We are doing update....")
                    TestCertsHistory.objects.filter(orion_id=self.orion_id).update(status="found")

    def save(self, *args, **kwargs):
        print("We are in Model.save")
        super(TestCertsData,self).save(*args, **kwargs)
        pk_val = self.pk
        print(pk_val)

        self.update_cert_history(pk_val)

class TestCertsHistory(models.Model):
    """TestCertsHistory. Model struture for NMap result diff response. """
    cert_id = models.IntegerField()
    orion_id = models.CharField(max_length=100, blank=True, null=True)
    md5 =  models.CharField(max_length=100, blank=True, null=True)
    status = models.CharField(max_length=100, blank=True, null=True)
    xml_data = models.TextField()

