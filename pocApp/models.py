from django.db import models
from django.forms import ModelForm
from django.urls import reverse
from datetime import date
from django.utils import timezone

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator

import datetime


# class MyCertsData(models.Model):
#     recid = models.AutoField(primary_key=True)
#     valid_start = models.CharField(max_length=100, blank=True, null=True)
#     valid_end = models.CharField(max_length=100, blank=True, null=True)
#     xmldata = models.TextField(verbose_name='??', null=True,)
#     status = models.CharField(max_length=100, blank=True, null=True)
#     hostname =  models.CharField(max_length=100, blank=True, null=True)
#     md5 =  models.CharField(max_length=100, blank=True, null=True)
#     sha1 =  models.CharField(max_length=100, blank=True, null=True)

class TestCertsData(models.Model):
    """TestCertsData. Model struture for NMap result response. """
    ip_value = models.CharField(max_length=100, blank=True, null=True)
    valid_start = models.DateTimeField(null=True, blank=True)
    valid_end = models.DateTimeField(null=True, blank=True)
    xmldata = models.TextField(verbose_name='??', null=True,)
    status = models.CharField(max_length=100, blank=True, null=True)
    hostname =  models.CharField(max_length=100, blank=True, null=True)
    commonName =  models.CharField(max_length=100, blank=True, null=True)
    organizationName =  models.CharField(max_length=100, blank=True, null=True)
    countryName =  models.CharField(max_length=100, blank=True, null=True)
    sig_algo =  models.CharField(max_length=100, blank=True, null=True)
    name =  models.CharField(max_length=100, blank=True, null=True)
    bits =  models.CharField(max_length=100, blank=True, null=True)
    md5 =  models.CharField(max_length=100, blank=True, null=True)
    sha1 =  models.CharField(max_length=100, blank=True, null=True)
    orion_id =  models.CharField(max_length=100, blank=True, null=True)


