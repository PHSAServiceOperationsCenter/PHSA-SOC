"""
ldap_probe.models
-----------------

This module contains the :class:`django.db.models.Model` models for the
:ref:`Domain Controllers Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Nov. 5, 2019

"""
import logging

from django.db import models
from django.utils.translation import gettext_lazy as _

from p_soc_auto_base.models import BaseModel


LOGGER = logging.getLogger('ldap_probe_log')


class NonOrionNode(BaseModel, models.Model):
    """
    """


class LdapProbeLog(models.Model):
    """
    """
