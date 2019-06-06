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
    list_per_page = 50

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
    list_display = ('uuid', 'event_group_id', 'event_type', 'event_status',
                    'mail_account', 'event_message', 'event_exception',
                    'source_host', 'show_site', 'event_registered_on')
    readonly_fields = ('uuid', 'event_type', 'event_status', 'source_host',
                       'event_registered_on', 'show_site', 'event_message',
                       'event_exception', 'event_group_id', 'mail_account',)
    list_filter = ('event_status', 'event_type',
                   'source_host__host_name', 'source_host__site__site',
                   ('event_registered_on', DateTimeRangeFilter),)

    def show_site(self, obj):  # pylint: disable=no-self-use
        """
        show the site
        """
        return obj.source_host.site.site
    show_site.short_description = 'site'

    def get_actions(self, request):
        """
        we don't need no actions for these events, they are controlled
        entirely by background processes
        """
        actions = super().get_actions(request)
        if 'enable_selected' in actions:
            del actions['enable_selected']
        if 'disable_selected' in actions:
            del actions['disable_selected']
        return actions


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

    def has_add_permission(self, request):  # @UnusedVariable
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
    list_display = ('event_uuid', 'event_group_id', 'mail_message_identifier',
                    'event_type', 'event_status', 'mail_account', 'event_message',
                    'sent_from', 'sent_to', 'source_host', 'show_site', )
    readonly_fields = ('event_uuid', 'event_group_id', 'event_type',
                       'event_status', 'mail_message_identifier', 'show_site',
                       'event_message', 'source_host', 'event_body',
                       'sent_from', 'sent_to', 'received_from', 'received_by',
                       'mail_message_created', 'mail_message_sent',
                       'mail_message_received', 'mail_account',
                       'sent_from', 'sent_to',)

    list_filter = ('event__event_status', 'event__event_type',
                   'event__source_host__host_name',
                   'event__source_host__site__site',
                   ('event__event_registered_on', DateTimeRangeFilter),)

# pylint: disable=no-self-use
    def show_site(self, obj):  # pylint: disable=no-self-use
        """
        show the site
        """
        return obj.event.source_host.site.site
    show_site.short_description = 'site'

    def event_uuid(self, obj):
        """
        show the event UUID, it is after all the primary key here
        """
        return obj.event.uuid
    event_uuid.short_description = 'UUID'

    def event_group_id(self, obj):
        """
        show the event group id
        """
        return obj.event.event_group_id
    event_group_id.short_description = 'Session ID'

    def event_type(self, obj):
        """
        show field from related model
        """
        return obj.event.event_type
    event_type.short_description = 'Event Type'

    def event_status(self, obj):
        """
        show field from related model
        """
        return obj.event.event_status
    event_status.short_description = 'Event Status'

    def event_message(self, obj):
        """
        show field from related model
        """
        return obj.event.event_message
    event_message.short_description = 'Event Message'

    def source_host(self, obj):
        """
        show field from related model
        """
        return obj.event.source_host
    source_host.short_description = 'Event Source Host'

    def event_body(self, obj):
        """
        show field from related model
        """
        return obj.event.event_body
    event_body.short_description = 'Raw Event Data'

    def mail_account(self, obj):
        """
        show field from related model
        """
        return obj.event.mail_account
    mail_account.short_description = 'Mail Account'
# pylint: enable=no-self-use

    def get_actions(self, request):
        """
        we don't need no actions for these events, they are controlled
        entirely by background processes
        """
        actions = super().get_actions(request)
        if 'enable_selected' in actions:
            del actions['enable_selected']
        if 'disable_selected' in actions:
            del actions['disable_selected']
        return actions
