"""
.. _admin:

django admin for the notifications app

:module:    p_soc_auto.notifications.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    sep. 26, 2018
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from rangefilter.filter import DateRangeFilter

from p_soc_auto_base.admin import BaseAdmin
from .models import (
    Notification, NotificationType, NotificationLevel, Broadcast,
    NotificationResponse, NotificationTypeBroadcast,
)


class NotificationsBaseAdmin(BaseAdmin, admin.ModelAdmin):
    """
    base admin class for the notifications app admin interface
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

        if db_field.name in ['notification_type', ]:
            kwargs['queryset'] = NotificationType.objects.\
                filter(enabled=True)

        if db_field.name in ['notification_level', ]:
            kwargs['queryset'] = NotificationLevel.objects.\
                filter(enabled=True)

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

    def get_readonly_fields(self, request, obj=None):
        """
        overload to make sure that some fields are always readonly
        """
        if obj is not None:
            return self.readonly_fields + \
                ('created_by', 'created_on', 'updated_on')

        return self.readonly_fields


class NotificationResponseTabAdmin(admin.TabularInline):
    model = NotificationResponse


@admin.register(Notification)
class NotificationAdmin(NotificationsBaseAdmin, admin.ModelAdmin):
    list_display_links = ('notification_uuid',)
    list_display = ('notification_uuid', 'enabled', 'rule_applies',
                    'notification_type',
                    'notification_level', 'created_on', 'broadcast_on',
                    'ack_on', 'esc_on', 'esc_ack_on')
    list_editable = ('enabled', 'notification_type', 'notification_level',)
    readonly_fields = ('message', 'broadcast_on',
                       'ack_on', 'esc_on', 'esc_ack_on')
    list_filter = ('enabled', 'notification_type__notification_type',
                   'notification_level__notification_level',
                   # TODO: need tighter filtering on content_type
                   'rule_applies__content_type__model',
                   ('created_on', DateRangeFilter),
                   ('broadcast_on', DateRangeFilter),
                   ('ack_on', DateRangeFilter),
                   ('esc_on', DateRangeFilter),
                   ('esc_ack_on', DateRangeFilter))

    inlines = [NotificationResponseTabAdmin, ]

    def has_add_permission(self, request):
        return False
