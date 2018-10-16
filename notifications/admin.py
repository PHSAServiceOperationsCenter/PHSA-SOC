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
    readonly_fields = ('created_on', 'updated_on')

    extra = 1
    max_num = 20
    show_change_link = True

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

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class NotificationTypeBroadcastTabAdmin(admin.TabularInline):
    model = NotificationTypeBroadcast
    readonly_fields = ('created_on', 'updated_on')

    extra = 1
    max_num = 20
    show_change_link = True

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

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(Notification)
class NotificationAdmin(NotificationsBaseAdmin, admin.ModelAdmin):
    list_display_links = ('notification_uuid',)
    list_display = ('notification_uuid', 'enabled', 'rule_applies',
                    'notification_type',
                    'notification_level', 'created_on', 'broadcast_on',
                    'ack_on', 'esc_on', 'esc_ack_on')
    list_editable = ('enabled', 'notification_type', 'notification_level',)
    readonly_fields = ('message', 'broadcast_on', 'rule_applies',
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
    search_fields = ('rule_msg', 'rule_applies__rule__rule',
                     'rule_applies__content_type__model', 'rule_msg')

    inlines = [NotificationResponseTabAdmin, ]

    def has_add_permission(self, request):
        """
        one is not allowed to create notifications manually
        """
        return False


@admin.register(NotificationResponse)
class NotificationResponseAdmin(NotificationsBaseAdmin, admin.ModelAdmin):
    """
    notification response admin forms
    """
    list_display_links = ('id',)
    list_display = ('id', 'notification', 'is_ack_message', 'notes',
                    'created_by',
                    'created_on', 'updated_by', 'updated_on', 'enabled')
    readonly_fields = ('id', 'created_on', 'updated_on', 'is_ack_message')
    list_filter = ('notification__notification_uuid', 'enabled',
                   ('created_on', DateRangeFilter))
    search_fields = ('notes',)

    def has_delete_permission(self, request, obj=None):
        """
        one is not supposed to delete notification responses
        """
        return False


@admin.register(NotificationType)
class NotificationTypeAdmin(NotificationsBaseAdmin, admin.ModelAdmin):
    """
    notification type admin forms
    """
    list_display = ('notification_type', 'enabled', 'is_default', 'ack_within',
                    'escalate_within', 'expire_within',
                    'expires_automatically', 'delete_if_expired', 'created_on',
                    'created_by')
    list_editable = ('enabled', 'is_default', 'ack_within',
                     'escalate_within', 'expire_within',
                     'expires_automatically', 'delete_if_expired')

    inlines = [NotificationTypeBroadcastTabAdmin, ]


@admin.register(Broadcast)
class BroadcastAdmin(NotificationsBaseAdmin, admin.ModelAdmin):
    """
    broadcast model admin forms
    """
    list_display = ('broadcast', 'is_default', 'enabled', 'created_by',
                    'created_on', 'updated_by', 'updated_on')
    list_editable = ('is_default', 'enabled')

    inlines = [NotificationTypeBroadcastTabAdmin, ]


@admin.register(NotificationLevel)
class NotificationLevelAdmin(NotificationsBaseAdmin, admin.ModelAdmin):
    """
    admin forms for the notification level model
    """
    list_display = ('notification_level', 'is_default', 'enabled',
                    'created_by', 'created_on', 'updated_by', 'updated_on')
    list_editable = ('is_default', 'enabled',)
