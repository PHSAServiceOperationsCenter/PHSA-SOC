"""
.. _admin:

django admin for the orion_integration app

:module:    p_soc_auto.orion_integration.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    aug. 8, 2018
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from rangefilter.filter import DateRangeFilter

from .models import (
    OrionNode, OrionNodeCategory, OrionAPMApplication, OrionCernerCSTNode,
)
from p_soc_auto_base.admin import BaseAdmin


class OrionBaseAdmin(BaseAdmin, admin.ModelAdmin):
    """
    admin methods that only apply to this application
    """

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        overload to populate updated_by from the request object
        """
        data = request.GET.copy()
        data['updated_by'] = request.user
        request.GET = data

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        overload
        admin.ModelAdmin.formfield_for_foreignkey(
            self, db_field, request, **kwargs)
        """
        if db_field.name in ['updated_by', ]:
            kwargs['queryset'] = get_user_model().objects.\
                filter(username=request.user.username)
            kwargs['initial'] = kwargs['queryset'].get()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

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

        if request.user.is_superuser:
            readonly_fields.remove('enabled')
            readonly_fields.remove('updated_by')

        return readonly_fields


@admin.register(OrionCernerCSTNode)
class OrionCernerCSTNodeAdmin(OrionBaseAdmin, admin.ModelAdmin):
    """
    admin interface for the OrionCernerCSTNode model
    """
    list_display = ['node_caption', 'enabled', 'orion_id',
                    'ip_address', 'category', 'machine_type', 'created_on',
                    'updated_on', 'not_seen_since', 'program_application',
                    'program_application_type', 'site', 'region']
    list_editable = ['enabled']
    list_filter = ['category__category', ('created_on', DateRangeFilter),
                   ('updated_on', DateRangeFilter),
                   ('not_seen_since', DateRangeFilter),
                   'program_application',
                   'program_application_type', 'site', 'region']
    search_fields = ['site', 'node_caption']


@admin.register(OrionNode)
class OrionNodeAdmin(OrionCernerCSTNodeAdmin, admin.ModelAdmin):
    """
    admin interface for the OrionNode model
    """
    pass


@admin.register(OrionNodeCategory)
class OrionNodeCategoryAdmin(OrionBaseAdmin, admin.ModelAdmin):
    """
    admin interface for the OrionNodeCategory model
    """
    list_display = ['category', 'enabled', 'orion_id',
                    'created_on',
                    'updated_on', 'not_seen_since', ]
    list_editable = ['enabled']
    list_filter = [('created_on', DateRangeFilter),
                   ('updated_on', DateRangeFilter),
                   ('not_seen_since', DateRangeFilter), ]


@admin.register(OrionAPMApplication)
class OrionAPMApplicationAdmin(OrionBaseAdmin, admin.ModelAdmin):
    """
    admin interface for the OrionAPApplication model
    """
    list_display = ['application_name', 'enabled', 'orion_id',
                    'node', 'full_name', 'created_on',
                    'updated_on', 'not_seen_since', 'status']
    list_editable = ['enabled']
    list_filter = ['node__site', 'node__category__category', 'status',
                   ('created_on', DateRangeFilter),
                   ('updated_on', DateRangeFilter),
                   ('not_seen_since', DateRangeFilter)]
    search_fields = ['application_name', 'full_name']
