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
    Subject, SubjectHeader, SubjectTag, Subscriber,
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

    def get_readonly_fields(self, request, obj=None):
        """
        overload to make sure that some fields are always readonly
        """
        if obj is not None:
            return self.readonly_fields + \
                ('created_on', 'updated_on', 'created_by', 'updated_by',)

        return self.readonly_fields


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


class SubjectHeaderInline(UhuruInlineBaseAdmin, admin.TabularInline):
    model = SubjectHeader

    fields = ('subject_header', 'enabled', 'created_by',
              'updated_by', 'updated_on', 'created_on',)
    readonly_fields = ('updated_on', 'created_on',)


class SubjectTagInline(admin.TabularInline):
    model = SubjectTag

    fields = ('subject_tag', 'enabled', 'created_by',
              'updated_by', 'updated_on', 'created_on',)
    readonly_fields = ('updated_on', 'created_on',)


@admin.register(Subject)
class SubjectAdmin(UhuruBaseAdmin, admin.ModelAdmin):
    list_display = ('subject', 'enabled',  'template_file', 'updated_on',
                    'updated_by',)
    list_editable = ('enabled',  'template_file',)
    list_filter = ('enabled',
                   ('created_on', DateRangeFilter),
                   ('updated_on', DateRangeFilter),)

    inlines = [SubjectHeaderInline, SubjectTagInline, ]


@admin.register(Subscriber)
class SubscriberAdmin(UhuruBaseAdmin, admin.ModelAdmin):
    pass