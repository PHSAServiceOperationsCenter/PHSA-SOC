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
from django.core import validators
from django.utils.translation import gettext_lazy as _

from p_soc_auto_base.models import BaseModel, BaseModelWithDefaultInstance
from p_soc_auto_base.utils import get_uuid


LOGGER = logging.getLogger('ldap_probe_log')


class LDAPBindCred(BaseModelWithDefaultInstance, models.Model):
    """
    :class:`django.db.models.Model` class used for storing credentials used
    for probing `Windows` domain controllers

    `LDAP Bind Credentials Set fields
    <../../../admin/doc/models/ldap_probe.ldapbindcred>`__
    """
    domain = models.CharField(
        _('windows domain'),
        max_length=15, db_index=True, blank=False, null=False,
        validators=[validators.validate_slug])
    username = models.CharField(
        _('domain username'),
        max_length=64, db_index=True, blank=False, null=False,
        validators=[validators.validate_slug])
    password = models.CharField(
        _('password'), max_length=64, blank=False, null=False)

    def __str__(self):
        return '%s\\%s' % (self.domain, self.username)

    class Meta:
        app_label = 'ldap_probe'
        constraints = [models.UniqueConstraint(
            fields=['domain', 'username'], name='unique_account')]
        indexes = [models.Index(fields=['domain', 'username'])]
        verbose_name = _('LDAP Bind Credentials Set')
        verbose_name_plural = _('LDAP Bind Credentials Sets')


class OrionNode(BaseModel, models.Model):
    """
    :class:`django.db.models.Model` class used for storing DNS information
    about `Windows` domain controller hosts defined on the `Orion`
    server

    `Domain Controller from Orion fields
    <../../../admin/doc/models/ldap_probe.orionnode>`__
    """
    node = models.OneToOneField(
        'orion_integration.OrionDomainControllerNode', db_index=True,
        blank=False, null=False, on_delete=models.PROTECT,
        verbose_name=_('Orion Node for Domain Controller'))
    ldap_bind_cred = models.ForeignKey(
        'ldap_probe.LDAPBindCred', db_index=True, blank=False, null=False,
        on_delete=models.PROTECT, verbose_name=_('LDAP Bind Credentials'))

    def __str__(self):
        if self.node.node_dns:
            return self.node.node_dns

        return self.node.node_caption

    class Meta:
        app_label = 'ldap_probe'
        verbose_name = _('Domain Controller from Orion')
        verbose_name_plural = _('Domain Controllers from Orion')


class NonOrionNode(BaseModel, models.Model):
    """
    :class:`django.db.models.Model` class used for storing DNS information
    about `Windows` domain controller hosts not available on the `Orion`
    server

    `Domain Controller not present in Orion fields
    <../../../admin/doc/models/ldap_probe.nonorionnode>`__
    """
    node_dns = models.CharField(
        _('FUlly Qualified Domain Name (FQDN)'), max_length=255,
        db_index=True, unique=True, blank=False, null=False,
        help_text=_(
            'The FQDN of the domain controller host. It must respect the'
            ' rules specified in'
            ' `RFC1123 <http://www.faqs.org/rfcs/rfc1123.html>`__,'
            ' section 2.1')
    )
    ldap_bind_cred = models.ForeignKey(
        'ldap_probe.LDAPBindCred', db_index=True, blank=False, null=False,
        on_delete=models.PROTECT, verbose_name=_('LDAP Bind Credentials'))

    def __str__(self):
        return self.node_dns

    def remove_if_in_orion(self):
        """
        if the domain controller host represented by this instance is also
        present on the `Orion` server, delete this istance

        We prefer to extract network node data from `Orion` instead of
        depending on some poor soul maintaining this model manually.
        """
        pass

    class Meta:
        app_label = 'ldap_probe'
        verbose_name = _('Domain Controller not present in Orion')
        verbose_name_plural = _('Domain Controllers not present in Orion')


class LdapProbeLog(models.Model):
    """
    :class:`django.db.models.Model` class used for storing LDAP probing
    information

    `LDAP Probe Log fields
    <../../../admin/doc/models/ldap_probe.ldapprobelog>`__
    """
    uuid = models.UUIDField(
        _('UUID'), unique=True, db_index=True, blank=False, null=False,
        default=get_uuid)
