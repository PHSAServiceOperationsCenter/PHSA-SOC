"""
ldap_probe.admin
-----------------

This module contains the `Django admin
<https://docs.djangoproject.com/en/2.2/ref/contrib/admin/#module-django.contrib.admin>`__
classes for the :ref:`Domain Controllers Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Nov. 22, 2019

"""
from django.contrib import admin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

from ldap_probe import models
from p_soc_auto_base import admin as base_admin


class LdapProbeBaseAdmin(base_admin.BaseAdmin, admin.ModelAdmin):
    """
    Base class for other :class:`Django admin classes
    <django.contrib.admin.ModelAdmin>` in this module
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        override
        :meth:`django.contrib.admin.ModelAdmin.formfield_for_foreignkey`

        provide specialized drop-down values for `created_by`, `updated_by`,
        `exchange_client_config`, and `site` `ForeignKey` fields.
        """
        if db_field.name in ['ldap_bind_cred', ]:
            kwargs['queryset'] = models.LDAPBindCred.objects.filter(
                enabled=True)
            kwargs['initial'] = models.LDAPBindCred.get_default()

        if db_field.name in ['ad_orion_node', ]:
            kwargs['queryset'] = models.OrionADNode.objects.filter(
                enabled=True)

        if db_field.name in ['ad_node', ]:
            kwargs['queryset'] = models.NonOrionADNode.objects.filter(
                enabled=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(models.OrionADNode)
class OrionADNodeAdmin(admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.OrionADNode`
    """


@admin.register(models.NonOrionADNode)
class NonOrionADNodeAdmin(LdapProbeBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.NonOrionADNode`
    """
    list_display = ('node_dns', 'enabled', 'ldap_bind_cred', 'created_on',
                    'updated_on', 'created_by', 'updated_by', )
    list_editable = ('enabled', 'ldap_bind_cred', )
    list_filter = ('enabled', 'ldap_bind_cred__domain',
                   'ldap_bind_cred__username', )
    search_fields = ('node_dns', )


@admin.register(models.LDAPBindCred)
class LDAPBindCredAdmin(admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.LDAPBindCred`
    """


@admin.register(models.LdapProbeLog)
class LdapProbeLogAdmin(admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.LdapProbeLog`
    """


@admin.register(models.LdapCredError)
class LdapCredErrorAdmin(admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.LdapCredError`
    """
