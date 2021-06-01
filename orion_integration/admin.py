"""
orion_integration.admin
-----------------------

This module contains the `Django admin` classes for the
:ref:`Orion Integration Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from rangefilter.filter import DateRangeFilter

from .models import (
    OrionNode, OrionNodeCategory, OrionAPMApplication, OrionCernerCSTNode,
    OrionDomainControllerNode,
)
from p_soc_auto_base.admin import BaseAdmin


class OrionBaseAdmin(BaseAdmin, admin.ModelAdmin):
    """
    Base :class:`django.contrib.admin.ModelAdmin` class for all the other
    classes in this module
    """

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

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        override
        :meth:`django.contrib.admin.ModelAdmin.formfield_for_foreignkey`

        provide specialized drop-down values for `created_by`, `updated_by`
        fields.
        """
        if db_field.name in ['updated_by', 'created_by']:
            kwargs['queryset'] = get_user_model().objects.\
                filter(username=request.user.username)
            kwargs['initial'] = kwargs['queryset'].get()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_add_permission(self, request):
        """
        override :meth:`django.contrib.admin.has_add_permission`

        All the data is maintained by background processes from the `Orion`
        server.
        Users are not allowed to create any records manually from the `Django
        admin` interface.
        """
        return False

    def get_readonly_fields(self, request, obj=None):
        """
        override :meth:`django.contrib.admin.ModelAdmin.get_readonly_fields`

        By default, all fields are read only. We make sure of this by
        pulling the fields from the underlying
        :class:`django.db.models.Model` model using the `Model _meta API
        <https://docs.djangoproject.com/en/2.2/ref/models/meta/#module-django.db.models.options>`__
        and placing them into the :attr:`readonly_fields` attribute of the
        :class:`django.contrib.admin.ModelAdmin` instance.

        However, superusers have full access to the `enabled` and the `updated_by`
        fields.

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
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`OrionCernerCSTNode` model
    """
    list_display = ['node_caption', 'enabled', 'orion_id',
                    'ip_address', 'category', 'machine_type', 'created',
                    'updated_on', 'not_seen_since', 'program_application',
                    'program_application_type', 'site', 'region']
    list_editable = ['enabled']
    list_filter = ['category__category', ('created', DateRangeFilter),
                   ('updated_on', DateRangeFilter),
                   ('not_seen_since', DateRangeFilter),
                   'program_application',
                   'program_application_type', 'site', 'region']
    search_fields = ['site', 'node_caption', 'node_dns', 'ip_address',
                     'program_application', 'program_application_type', ]


@admin.register(OrionNode)
class OrionNodeAdmin(OrionCernerCSTNodeAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`OrionNode` model
    """


@admin.register(OrionDomainControllerNode)
class OrionDomainControllerNodeAdmin(
        OrionCernerCSTNodeAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`OrionDomainControllerNode` model
    """


@admin.register(OrionNodeCategory)
class OrionNodeCategoryAdmin(OrionBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`OrionNodeCategory` model
    """
    list_display = ['category', 'enabled', 'orion_id',
                    'created',
                    'updated_on', 'not_seen_since', ]
    list_editable = ['enabled']
    list_filter = [('created', DateRangeFilter),
                   ('updated_on', DateRangeFilter),
                   ('not_seen_since', DateRangeFilter), ]


@admin.register(OrionAPMApplication)
class OrionAPMApplicationAdmin(OrionBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`OrionAPMApplication` model
    """
    list_display = ['application_name', 'enabled', 'orion_id',
                    'node', 'full_name', 'created',
                    'updated_on', 'not_seen_since', 'status']
    list_editable = ['enabled']
    list_filter = ['node__site', 'node__category__category', 'status',
                   ('created', DateRangeFilter),
                   ('updated_on', DateRangeFilter),
                   ('not_seen_since', DateRangeFilter)]
    search_fields = ['application_name', 'full_name']
