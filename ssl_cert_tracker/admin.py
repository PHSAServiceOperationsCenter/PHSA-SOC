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

from .models import NmapCertsData, SslExpiresIn, SslHasExpired, SslNotYetValid
from p_soc_auto_base.admin import BaseAdmin


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
                    'not_after', 'node_admin_url', 'orion_node_url', 'bits',
                    'md5', 'sha1', 'updated_on']
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
                    'orion_node_url', 'bits', 'md5', 'sha1', 'updated_on']

    def expires_in_days(self, obj):
        return 'expires in %s days' % obj.expires_in
    expires_in_days.short_description = 'expires in'


@admin.register(SslHasExpired)
class SslHasExpiredAdmin(NmapCertsDataAdmin):
    """
    only expired SSL certificates sorted by expiration date ascending
    """

    def has_expired_days_ago(self, obj):
        return 'has expired %s days ago' % obj.expired
    has_expired_days_ago.short_description = 'has expired'


@admin.register(SslNotYetValid)
class SslNotYetValiddAdmin(NmapCertsDataAdmin):
    """
    only not yet valid SSL certificates sorted by expiration date ascending
    """
    pass
