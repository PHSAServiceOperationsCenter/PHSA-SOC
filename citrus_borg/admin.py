"""
.. _admin:

django admin module for the citrus_borg app

:module:    citrus_borg.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    nov. 126, 2018

"""
from django.contrib import admin
from django.contrib.auth import get_user_model

from p_soc_auto_base.admin import BaseAdmin
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

from .models import (
    WinlogEvent, WinlogbeatHost, KnownBrokeringDevice, BorgSite,
    BorgSiteNotSeen, WinlogbeatHostNotSeen, KnownBrokeringDeviceNotSeen,
)


class CitrusBorgBaseAdmin(BaseAdmin, admin.ModelAdmin):
    """
    base admin class for the citrus_borg application
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        overload
        admin.ModelAdmin.formfield_for_foreignkey(
            self, db_field, request, **kwargs)
        """
        if db_field.name in ['created_by', 'updated_by', ]:
            kwargs['queryset'] = get_user_model().objects.\
                filter(username=request.user.username)
            kwargs['initial'] = kwargs['queryset'].get()

        if db_field.name in ['site', ]:
            kwargs['queryset'] = BorgSite.objects.filter(enabled=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        """
        overload to populate the user fields from the request object
        """
        data = request.GET.copy()
        data['created_by'] = request.user
        data['updated_by'] = request.user
        request.GET = data

        return super().add_view(
            request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        overload to populate updated_by from the request object
        """
        data = request.GET.copy()
        data['updated_by'] = request.user
        request.GET = data

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)

    def get_readonly_fields(self, request, obj=None):  # @UnusedVariable
        """
        overload to make sure that some fields are always readonly
        """
        if obj is not None:
            return self.readonly_fields + \
                ('created_by', 'created_on', 'updated_on')

        return self.readonly_fields


@admin.register(BorgSite)
class BorgSiteAdmin(CitrusBorgBaseAdmin, admin.ModelAdmin):
    """
    admin class for borg sites
    """
    list_display = ('site', 'enabled', 'notes',
                    'last_seen', 'updated_on', 'updated_by')
    list_editable = ('notes', 'enabled',)
    list_filter = ('enabled',)
    readonly_fields = ('last_seen',)

    def last_seen(self, obj):
        return obj.winlogbeathost_set.first().last_seen
    last_seen.short_description = 'last seen'


@admin.register(BorgSiteNotSeen)
class BorgSiteNotSeenAdmin(BorgSiteAdmin):
    pass


@admin.register(KnownBrokeringDevice)
class KnownBrokeringDeviceAdmin(CitrusBorgBaseAdmin, admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display = ('broker_name',  'enabled', 'last_seen', 'created_on',)
    list_editable = ('enabled',)
    list_filter = ('enabled',)
    readonly_fields = ('broker_name', 'last_seen', 'created_on',)


@admin.register(KnownBrokeringDeviceNotSeen)
class KnownBrokeringDeviceNotSeenAdmin(KnownBrokeringDeviceAdmin):
    pass


@admin.register(WinlogbeatHost)
class WinlogbeatHostAdmin(CitrusBorgBaseAdmin, admin.ModelAdmin):

    list_display = ('host_name', 'ip_address',  'enabled', 'site',
                    'resolved_fqdn', 'last_seen', 'created_on',)
    list_editable = ('site', 'enabled',)
    readonly_fields = ('host_name', 'ip_address', 'resolved_fqdn', 'last_seen',
                       'created_on',)
    list_filter = ('site__site', 'enabled',)


@admin.register(WinlogbeatHostNotSeen)
class WinlogbeatHostNotSeenAdmin(WinlogbeatHostAdmin):
    pass


@admin.register(WinlogEvent)
class WinlogEventAdmin(CitrusBorgBaseAdmin, admin.ModelAdmin):

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    list_display_links = ('uuid',)
    list_display = (
        'uuid', 'is_expired', 'event_state', 'source_host', 'xml_broker',
        'event_test_result', 'storefront_connection_duration',
        'receiver_startup_duration', 'connection_achieved_duration',
        'logon_achieved_duration', 'logoff_achieved_duration', 'created_on',
    )
    list_editable = ('is_expired',)
    readonly_fields = (
        'uuid', 'event_state', 'source_host', 'xml_broker',
        'event_test_result', 'record_number', 'windows_log', 'failure_reason',
        'failure_details', 'storefront_connection_duration',
        'receiver_startup_duration', 'connection_achieved_duration',
        'logon_achieved_duration', 'logoff_achieved_duration',
    )
    list_filter = ('event_state', 'source_host__host_name',
                   'source_host__site__site',
                   'xml_broker__broker_name',
                   ('created_on', DateTimeRangeFilter),
                   'is_expired',)
