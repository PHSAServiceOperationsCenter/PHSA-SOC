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

from mail_collector.models import MailBotLogEvent, MailBotMessage
from citrus_borg.models import BorgSite


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
        return obj.source_host.site.site
    show_site.short_description = 'site'
