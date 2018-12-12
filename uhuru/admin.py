"""
.. _admin:

django admin module for the uhuru app

:module:    uhuru.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Dec. 10, 2018

"""
from django.contrib import admin
from django.contrib.auth import get_user_model

from rangefilter.filter import DateRangeFilter

from p_soc_auto_base.admin import BaseAdmin

from .models import (
    Subject, SubjectHeader, SubjectTag, Subscriber, SubscriberGroup,
    EmailAddress, Telephone,
)


class UhuruBaseAdmin(BaseAdmin, admin.ModelAdmin):
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


class UhuruInlineBaseAdmin(admin.TabularInline):
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


@admin.register(EmailAddress)
class EmailAddressAdmin(UhuruBaseAdmin, admin.ModelAdmin):
    list_display = ('email_address', 'subscriber',
                    'enabled', 'updated_on', 'updated_by')
    list_editable = ('subscriber', 'enabled',)
    list_filter = ('subscriber__subscriber__username',
                   'subscriber__subscriber__first_name',
                   'subscriber__subscriber__last_name', 'enabled',
                   ('updated_on', DateRangeFilter), )
    search_fields = ['email_address', 'subscriber__subscriber__username',
                     'subscriber__subscriber__first_name',
                     'subscriber__subscriber__last_name', ]
    readonly_fields = ('created_on', 'updated_on', )

    fieldsets = (
        ('Identification', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('enabled', 'email_address', 'subscriber', ), ),
        }, ),
        ('Description', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': ('notes', ),
        }, ),
        ('History', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': (('created_on', 'created_by', ),
                       ('updated_on', 'updated_by', ),),
        }, ),
    )


@admin.register(Telephone)
class TelephoneAdmin(UhuruBaseAdmin, admin.ModelAdmin):
    list_display = ('telephone', 'subscriber', 'is_sms',
                    'enabled', 'updated_on', 'updated_by')
    list_editable = ('subscriber', 'enabled', 'is_sms',)
    list_filter = ('subscriber__subscriber__username',
                   'subscriber__subscriber__first_name',
                   'subscriber__subscriber__last_name', 'is_sms', 'enabled',
                   ('updated_on', DateRangeFilter), )
    search_fields = ['email_address', 'subscriber__subscriber__username',
                     'subscriber__subscriber__first_name',
                     'subscriber__subscriber__last_name', ]
    readonly_fields = ('created_on', 'updated_on', )

    fieldsets = (
        ('Identification', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('enabled', 'telephone', 'is_sms', 'subscriber', ), ),
        }, ),
        ('Description', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': ('notes', ),
        }, ),
        ('History', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': (('created_on', 'created_by', ),
                       ('updated_on', 'updated_by', ),),
        }, ),
    )


@admin.register(Subject)
class SubjectAdmin(UhuruBaseAdmin, admin.ModelAdmin):
    list_display = ('subject', 'enabled',  'template_file', 'updated_on',
                    'updated_by',)
    list_editable = ('enabled',  'template_file',)
    list_filter = ('enabled',
                   ('created_on', DateRangeFilter),
                   ('updated_on', DateRangeFilter),)
    search_fields = ['subject', 'template_file', ]
    readonly_fields = ('created_on', 'updated_on', )

    filter_horizontal = ('headers', 'tags',)

    fieldsets = (
        ('Identification', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('enabled', 'subject', 'template_file', ), ),
        }, ),
        ('Description', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': ('notes', ),
        }, ),
        ('Field Headers', {
            'classes': ('wide', 'extrapretty', ),
            'fields': (('headers', ), ),
        }, ),
        ('Subject Tags', {
            'classes': ('grp-collapse grp-open', ),
            'fields': (('tags', ), ),
        }, ),
        ('History', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': (('created_on', 'created_by', ),
                       ('updated_on', 'updated_by', ),),
        }, ),
    )


@admin.register(SubjectHeader)
class SubjectHeaderAdmin(UhuruBaseAdmin, admin.ModelAdmin):
    list_display = ('subject_header', 'enabled', 'used_for', 'created_on',
                    'updated_on', 'created_by', 'updated_by',)
    list_editable = ('enabled', )
    list_filter = ('enabled',
                   ('created_on', DateRangeFilter),
                   ('updated_on', DateRangeFilter),)
    search_fields = ['subject_header', ]
    readonly_fields = ('created_on', 'updated_on', 'used_for',)

    fieldsets = (
        ('Identification', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('enabled', 'subject_header', ), ('used_for', ), ),
        }, ),
        ('Description', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': ('notes', ),
        }, ),
        ('History', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': (('created_on', 'created_by', ),
                       ('updated_on', 'updated_by', ),),
        }, ),
    )


@admin.register(SubjectTag)
class SubjectTagAdmin(UhuruBaseAdmin, admin.ModelAdmin):
    list_display = ('subject_tag', 'enabled', 'used_for', 'created_on',
                    'updated_on', 'created_by', 'updated_by',)
    list_editable = ('enabled', )
    list_filter = ('enabled',
                   ('created_on', DateRangeFilter),
                   ('updated_on', DateRangeFilter),)
    search_fields = ['subject_tag', ]
    readonly_fields = ('created_on', 'updated_on', 'used_for',)

    fieldsets = (
        ('Identification', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('enabled', 'subject_tag', ), ('used_for', ), ),
        }, ),
        ('Description', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': ('notes', ),
        }, ),
        ('History', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': (('created_on', 'created_by', ),
                       ('updated_on', 'updated_by', ),),
        }, ),
    )


@admin.register(Subscriber)
class SubscriberAdmin(UhuruBaseAdmin, admin.ModelAdmin):
    list_display = ('subscriber', 'name', 'primary_email', 'enabled',
                    'updated_on', 'updated_by')
    readonly_fields = ('name', 'primary_email', 'created_on',
                       'updated_on', 'belongs_to', )
    list_editable = ('enabled',)
    list_filter = ('subscribergroup__subscriber_group', 'enabled',
                   ('created_on', DateRangeFilter),
                   ('updated_on', DateRangeFilter),)
    search_fields = ['subscriber__username', 'subscriber__last_name',
                     'subscriber__first_name', 'subscriber__email', ]
    readonly_fields = ('created_on', 'updated_on', 'name', 'primary_email',
                       'belongs_to', )

    fieldsets = (
        ('Identification', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('enabled', 'subscriber', ),
                       ('name', 'primary_email', 'belongs_to', ), ),
        }, ),
        ('Description', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': ('notes', ),
        }, ),
        ('History', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': (('created_on', 'created_by', ),
                       ('updated_on', 'updated_by', ),),
        }, ),
    )


@admin.register(SubscriberGroup)
class SubscriberGroupAdmin(UhuruBaseAdmin, admin.ModelAdmin):
    list_display = ('subscriber_group', 'enabled', 'group_email_address',
                    'group_pager', 'updated_on', 'updated_by')
    list_editable = ('enabled', 'group_email_address', 'group_pager',)
    list_filter = ('enabled',
                   ('created_on', DateRangeFilter),
                   ('updated_on', DateRangeFilter),)
    search_fields = ['subscriber_group',
                     'group_email_address', 'group_pager', ]
    filter_horizontal = ('subscriber', )
    readonly_fields = ('created_on', 'updated_on', )

    fieldsets = (
        ('Identification', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('enabled', 'subscriber_group', ),
                       ('group_email_address', 'group_pager', ), ),
        }, ),
        ('Description', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': ('notes', ),
        }, ),
        ('Members', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('subscriber', ), ),
        }, ),
        ('History', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': (('created_on', 'created_by', ),
                       ('updated_on', 'updated_by', ),),
        }, ),
    )
