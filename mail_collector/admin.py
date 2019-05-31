"""
.. _admin:

django admin forms for the mail_collector app

:module:    mail_collector.admin

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    may 30, 2019

"""
from django.contrib import admin

from rangefilter.filter import DateTimeRangeFilter

from mail_collector.models import MailBotLogEvent, MailBotMessage, MailHost
from citrus_borg.models import BorgSite
from citrus_borg.admin import CitrusBorgBaseAdmin


class MailBotAdmin(admin.ModelAdmin):
    """
    base class
    """

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name in ['site', ]:
            kwargs['queryset'] = BorgSite.objects.filter(enabled=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(MailBotLogEvent)
class MailBotLogEventAdmin(MailBotAdmin, admin.ModelAdmin):
    """
    admin forms for mail bot log events
    """
    list_display_links = ('uuid',)
    list_display = ('uuid', 'event_type', 'event_status', 'event_message',
                    'event_exception', 'source_host',
                    'show_site', 'event_registered_on')
    readonly_fields = ('uuid', 'event_type', 'event_status', 'source_host',
                       'event_registered_on', 'show_site', 'event_message',
                       'event_exception',)
    list_filter = ('event_status', 'event_type',
                   'source_host__host_name', 'source_host__site__site',
                   ('event_registered_on', DateTimeRangeFilter),)

    def show_site(self, obj):
        """
        show the site
        """
        return obj.source_host.site.site
    show_site.short_description = 'site'


@admin.register(MailHost)
class MailHostAdmin(CitrusBorgBaseAdmin, admin.ModelAdmin):
    """
    admin forms for exchange monitoring bots
    """
    list_display = ('host_name', 'ip_address', 'orion_id', 'enabled', 'site',
                    'resolved_fqdn', 'excgh_last_seen', 'created_on',)
    list_editable = ('site', 'enabled',)
    readonly_fields = ('host_name', 'ip_address', 'resolved_fqdn',
                       'excgh_last_seen', 'created_on', 'orion_id',)
    list_filter = ('site__site', 'enabled',
                   ('excgh_last_seen', DateTimeRangeFilter),)
    search_fields = ('site__site', 'host_name', 'ip_address')

    def has_add_permission(self, request):
        """
        these bots are created from data collected via logstash.
        adding manually will just add more noise to the database
        """
        return False


@admin.register(MailBotMessage)
class MailBotMessageAdmin(MailBotAdmin, admin.ModelAdmin):
    """
    admin ofrms for exchange monitoring events that include a mail message
    """
    list_display_links = ('event_uuid',)
    list_display = ('event_uuid',
                    'show_site', )
    readonly_fields = ('event_uuid', )

    list_filter = ('event__event_status', 'event__event_type',
                   'event__source_host__host_name',
                   'event__source_host__site__site',
                   ('event__event_registered_on', DateTimeRangeFilter),)

    def show_site(self, obj):
        """
        show the site
        """
        return obj.event.source_host.site.site
    show_site.short_description = 'site'

    def event_uuid(self, obj):
        return obj.event.uuid
    event_uuid.short_description = 'UUID'
