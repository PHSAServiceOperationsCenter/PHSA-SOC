"""
citrus_borg.admin
-----------------

This module contains the `Django admin` classes for the
:ref:`Citrus Borg Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

from p_soc_auto_base.admin import BaseAdmin
from .models import (
    WinlogEvent, WinlogbeatHost, KnownBrokeringDevice, BorgSite,
    BorgSiteNotSeen, WinlogbeatHostNotSeen, KnownBrokeringDeviceNotSeen,
    AllowedEventSource, CitrixHost
)
from mail_collector.models import ExchangeConfiguration


class CitrusBorgBaseAdmin(BaseAdmin, admin.ModelAdmin):
    """
    Base :class:`django.contrib.admin.ModelAdmin` class for all the other
    classes in this module
    """
    list_per_page = 50

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        override
        :meth:`django.contrib.admin.ModelAdmin.formfield_for_foreignkey`

        provide specialized drop-down values for `created_by`, `updated_by`,
        `exchange_client_config`, and `site` `ForeignKey` fields.
        """
        if db_field.name in ['created_by', 'updated_by', ]:
            kwargs['queryset'] = get_user_model().objects.\
                filter(username=request.user.username)
            kwargs['initial'] = kwargs['queryset'].get()

        elif db_field.name == 'site':
            kwargs['queryset'] = BorgSite.active

        elif db_field.name == 'exchange_client_config':
            kwargs['queryset'] = ExchangeConfiguration.active
            kwargs['initial'] = ExchangeConfiguration.get_default()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        """
        override :meth:`django.contrib.admin.ModelAdmin.add_view`

        pre-populate `created_by` and `updated_by` from the :attr:`user` attribute
        of the `request` object.
        """
        data = request.GET.copy()
        data['created_by'] = request.user
        data['updated_by'] = request.user
        request.GET = data

        return super().add_view(
            request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        override :meth:`django.contrib.admin.ModelAdmin.change_view`

        pre-populate `updated_by` from the :attr:`user` attribute
        of the `request` object.
        """
        data = request.GET.copy()
        data['updated_by'] = request.user
        request.GET = data

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)

    def get_readonly_fields(self, request, obj=None):  # @UnusedVariable
        """
        override
        :meth:`django.contrib.admin.ModelAdmin.get_readonly_fields`.

        Make sure that the 'created_by', 'created_on', and 'updated_on' fields
        are always read only.
        """
        if obj is not None:
            return self.readonly_fields + \
                ('created_by', 'created_on', 'updated_on')

        return self.readonly_fields


@admin.register(AllowedEventSource)
class AllowedEventSourceAdmin(CitrusBorgBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`citrus_borg.models.AllowedEventSource`
    """
    list_display = ('source_name', 'enabled', 'notes',
                    'updated_on', 'updated_by')
    list_editable = ('notes', 'enabled',)
    list_filter = ('enabled',)


@admin.register(BorgSite)
class BorgSiteAdmin(CitrusBorgBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`citrus_borg.models.BorgSite`
    """
    list_display = ('site', 'enabled', 'notes',
                    'last_seen', 'excgh_last_seen', 'updated_on', 'updated_by')
    list_editable = ('notes', 'enabled',)
    list_filter = ('enabled',)
    readonly_fields = ('last_seen', 'excgh_last_seen',)

    def last_seen(self, obj):  # pylint: disable=no-self-use
        """
        calculated display for :attr:`field
        <citrus_borg.models.BorgSite.last_seen>`

        Warns the user to allocate at least one
        :class:`citrus_borg.models.WinlogbeatHost` instance pointing to a
        remote host running `ControlUp`.
        """
        first_bot = obj.winlogbeathost_set.\
            filter(last_seen__isnull=False).first()
        if first_bot:
            return first_bot.last_seen
        return 'Please allocate at least one Citrix bot to this site'
    last_seen.short_description = 'last seen'

    def excgh_last_seen(self, obj):  # pylint: disable=no-self-use
        """
        calculated display for :attr:`field
        <citrus_borg.models.BorgSite.excgh_last_seen>`

        Warns the user to allocate at least one
        :class:`citrus_borg.models.WinlogbeatHost` instance pointing to a
        remote host running the :ref:`Mail Borg Client Application`.

        """
        first_bot = obj.winlogbeathost_set.\
            filter(excgh_last_seen__isnull=False).first()

        if first_bot:
            return first_bot.excgh_last_seen
        return 'Please allocate at least one Exchange client bot to this site'
    excgh_last_seen.short_description = 'Exchange client bot last seen'


@admin.register(BorgSiteNotSeen)
class BorgSiteNotSeenAdmin(BorgSiteAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`citrus_borg.models.BorgSiteNotSeen`
    """


@admin.register(KnownBrokeringDevice)
class KnownBrokeringDeviceAdmin(CitrusBorgBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`citrus_borg.models.KnownBrokeringDevice`
    """

    def has_add_permission(self, request):  # @UnusedVariable
        """
        override :meth:`django.contrib.admin.has_add_permission`.

        Nobody is allowed to create any instance using this class.
        All the data is maintained by background processes.
        """
        return False

    def has_delete_permission(self, request, obj=None):  # @UnusedVariable
        """
        override :meth:`django.contrib.admin.has_delete_permission`

        Nobody is allowed to delete any instance using this class.
        All the data is maintained by background processes.
        """
        return False

    list_display = ('broker_name',  'enabled', 'last_seen', 'created_on',)
    list_editable = ('enabled',)
    list_filter = ('enabled',)
    readonly_fields = ('broker_name', 'last_seen', 'created_on',)


@admin.register(KnownBrokeringDeviceNotSeen)
class KnownBrokeringDeviceNotSeenAdmin(KnownBrokeringDeviceAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`citrus_borg.models.KnownBrokeringDeviceNotSeen`
    """


@admin.register(CitrixHost)
class WinlogbeatHostAdmin(CitrusBorgBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`citrus_borg.models.WinlogbeatHost`
    """
    list_display = ('host_name', 'ip_address', 'orion_id', 'enabled', 'site',
                    'exchange_client_config', 'resolved_fqdn', 'last_seen',
                    'created_on',)
    list_editable = ('site', 'enabled', 'exchange_client_config',)
    readonly_fields = ('host_name', 'ip_address', 'resolved_fqdn', 'last_seen',
                       'created_on', 'orion_id',)
    list_filter = ('site__site', 'enabled', 'exchange_client_config__is_default',
                   ('last_seen', DateTimeRangeFilter),)
    search_fields = ('site__site', 'host_name', 'ip_address',
                     'exchange_client_config__config_name',)

    def has_add_permission(self, request):  # @UnusedVariable
        """
        override :meth:`django.contrib.admin.has_add_permission`.

        Nobody is allowed to create any instance using this class.
        Bots are created and maintained by background processes.

        """
        return False


@admin.register(WinlogbeatHostNotSeen)
class WinlogbeatHostNotSeenAdmin(WinlogbeatHostAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`citrus_borg.models.WinlogbeatHostNotSeen`
    """
    pass


@admin.register(WinlogEvent)
class WinlogEventAdmin(CitrusBorgBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`citrus_borg.models.WinlogEvent`
    """

    def has_add_permission(self, request):
        """
        override :meth:`django.contrib.admin.has_add_permission`.

        Nobody is allowed to create any instance using this class.
        Events are created and maintained by background processes.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        override :meth:`django.contrib.admin.has_delete_permission`.

        Nobody is allowed to delete any instance using this class.
        Events are deleted by background processes.
        """
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
