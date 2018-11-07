"""
.. _admin:

django admin for the ssl_cert_tracker app

:module:    p_soc_auto.ssl_cert_tracker.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

:updated:    sep. 21, 2018
"""
from django.contrib import admin
from rangefilter.filter import DateRangeFilter

from simple_history.admin import SimpleHistoryAdmin

from .models import (
    NmapCertsData, SslExpiresIn, SslHasExpired, SslNotYetValid, Subscription,
)
from p_soc_auto_base.admin import BaseAdmin


@admin.register(Subscription)
class Subscription(BaseAdmin, admin.ModelAdmin):
    def has_add_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        return False

    list_display = ['subscription', 'enabled', 'emails_list', 'template_dir',
                    'template_name', 'template_prefix', 'updated_on',
                    'updated_by']
    list_editable = ['enabled', 'emails_list', 'template_dir',
                     'template_name', 'template_prefix']
    readonly_fields = ['created_on', 'updated_on', ]


class SSLCertTrackerBaseAdmin(BaseAdmin, admin.ModelAdmin):
    """
    base class for admin classes in this application
    """

    def has_add_permission(self, request, obj=None):
        """
        all these things are populated from orion

        do not allow any tom, dick, and harriet to add stuff on their own
        """
        return False

    def get_readonly_fields(self, request, obj=None):
        """
        overload get_readonly_fields

        for superusers we want enabled as a regular field and everything
        else readonly

        for everybody else we want everything to be readonly
        """
        readonly_fields = list(self.readonly_fields)
        readonly_fields += [field.name for field in self.model._meta.fields]

        return readonly_fields


@admin.register(NmapCertsData)
class NmapCertsDataAdmin(SSLCertTrackerBaseAdmin, SimpleHistoryAdmin):
    """
    SSL certificate data admin pages
    """
    list_display = ['common_name', 'organization_name', 'not_before',
                    'not_after', 'node_admin_url', 'orion_node_url',
                    'updated_on']
    history_list_display = ['updated_on', ]
    list_filter = [('not_after', DateRangeFilter),
                   ('not_before', DateRangeFilter),
                   ('updated_on', DateRangeFilter)]
    search_fields = ['common_name', 'organization_name']
    readonly_fields = ['node_admin_url', 'orion_node_url', ]


@admin.register(SslExpiresIn)
class SslExpiresInAdmin(NmapCertsDataAdmin):
    """
    only valid SSL certificates sorted by expiration date ascending
    """
    readonly_fields = ('expires_in_days',)
    list_display = ['common_name', 'organization_name', 'expires_in_days',
                    'not_before', 'not_after', 'node_admin_url',
                    'orion_node_url', 'updated_on']

    def expires_in_days(self, obj):
        return obj.expires_in_x_days
    expires_in_days.short_description = 'expires in X days'


@admin.register(SslHasExpired)
class SslHasExpiredAdmin(NmapCertsDataAdmin):
    """
    only expired SSL certificates sorted by expiration date ascending
    """
    readonly_fields = ('has_expired_days_ago',)
    list_display = ['common_name', 'organization_name',
                    'has_expired_days_ago',
                    'not_before', 'not_after', 'node_admin_url',
                    'orion_node_url', 'updated_on']

    def has_expired_days_ago(self, obj):
        return obj.has_expired_x_days_ago
    has_expired_days_ago.short_description = 'has expired X days ago'


@admin.register(SslNotYetValid)
class SslNotYetValiddAdmin(NmapCertsDataAdmin):
    """
    only not yet valid SSL certificates sorted by expiration date ascending
    """
    readonly_fields = ('valid_in_days',)
    list_display = ['common_name', 'organization_name',
                    'valid_in_days',
                    'not_before', 'not_after', 'node_admin_url',
                    'orion_node_url', 'updated_on']

    def valid_in_days(self, obj):
        return obj.will_become_valid_in_x_days
    valid_in_days.short_description = 'will become valid in X days'
