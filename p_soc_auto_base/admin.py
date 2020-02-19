"""
.. _base_admin:

:module:    p_soc_auto.p_soc_auto_base.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

`django.contrib.admin` objects to be reused across the :ref:`SOC Automation
Server` apps

"""
import socket

from django.conf import settings
from django.contrib import admin
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import FieldDoesNotExist
from django.utils import timezone

from djqscsv import write_csv

from citrus_borg.models import BorgSite
from mail_collector.models import ExchangeConfiguration

admin.site.site_header = 'SOC Automation Server'
admin.site.index_title = 'SOC Automation Server Administration'


def enable_selected(modeladmin, request, queryset):
    """
    add an action to the `Django Admin Summary pages` that will set an
    :attr:`enabled` field to ``True`` if the
    :class:`Django model <django.db.models.Model>` behind a
    :class:`Django admin <django.contrib.admin.ModelAdmin>` has such an
    attribute

    See `Django admin actions
    <https://docs.djangoproject.com/en/2.2/ref/contrib/admin/actions/>`_.
    """
    try:
        modeladmin.model._meta.get_field('enabled')
    except FieldDoesNotExist as err:
        modeladmin.message_user(request, str(err), level=messages.ERROR)
        return

    rows_enabled = queryset.update(enabled=True)
    if rows_enabled == 1:
        msg = '1 %s was enabled' % modeladmin.model._meta.verbose_name
    else:
        msg = '%s %s were enabled' % (
            rows_enabled, modeladmin.model._meta.verbose_name_plural)

    modeladmin.message_user(request, msg, level=messages.INFO)
    return


enable_selected.short_description = 'Enable selected'

admin.site.add_action(enable_selected, 'enable_selected')


def disable_selected(modeladmin, request, queryset):
    """
    add an action to the `Django Admin Summary pages` that will set an
    :attr:`enabled` field to ``False`` if the
    :class:`Django model <django.db.models.Model>` behind a
    :class:`Django admin <django.contrib.admin.ModelAdmin>` has such an
    attribute
    """
    try:
        modeladmin.model._meta.get_field('enabled')
    except FieldDoesNotExist as err:
        modeladmin.message_user(request, str(err), level=messages.ERROR)
        return

    rows_enabled = queryset.update(enabled=False)
    if rows_enabled == 1:
        msg = '1 %s was disabled' % modeladmin.model._meta.verbose_name
    else:
        msg = '%s %s were disabled' % (
            rows_enabled, modeladmin.model._meta.verbose_name_plural)

    modeladmin.message_user(request, msg, level=messages.INFO)
    return


disable_selected.short_description = 'Disable selected'

admin.site.add_action(disable_selected, 'disable_selected')


def export_to_csv(modeladmin, request, queryset):
    """
    add an action to export the queryset behind an admin summary page to csv
    """
    field_names = []
    if hasattr(queryset.model, 'csv_fields'):
        field_names = queryset.model.csv_fields

    csv_file_name = (f'{settings.EXPORT_CSV_MEDIA_ROOT}'
                     f'{timezone.localtime():%Y_%m_%d-%H_%M_%S}-'
                     f'{queryset.model._meta.verbose_name}.csv')

    with open(csv_file_name, 'wb') as csv_file:
        try:
            write_csv(queryset.values(*field_names), csv_file)
        except Exception as error:
            modeladmin.message_user(
                request,
                f'cannot export the data in the'
                f' {queryset.model._meta.verbose_name} queryset to csv:'
                f' {str(error)}', level=messages.ERROR)
            return

    modeladmin.message_user(
        request,
        f'Data exported to {socket.getfqdn()}:/{csv_file_name}',
        level=messages.INFO)


export_to_csv.short_description = 'Export to CSV file'
admin.site.add_action(export_to_csv, 'export_to_csv')


class BaseAdmin(admin.ModelAdmin):
    """
    Use this class as the base class for other admin classes inheriting from
    :class:`django.contrib.admin.ModelAdmin` if so desired
    """
    actions_on_top = True
    actions_on_bottom = True
    actions_selection_counter = True
    save_on_top = True
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
            kwargs['initial'] = ExchangeConfiguration.default()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        """
        override :meth:`django.contrib.admin.ModelAdmin.add_view`

        pre-populate `created_by` and `updated_by` from the :attr:`user`
        attribute of the `request` object.
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

        pre-populate `updated_by` from the :attr:`user` attribute of the
        `request` object.
        """
        data = request.GET.copy()
        data['updated_by'] = request.user
        request.GET = data

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)

    def get_readonly_fields(self, request, obj=None):  # @UnusedVariable
        """
        override :meth:`django.contrib.admin.ModelAdmin.get_readonly_fields`

        Make sure that the 'created_by', 'created_on', and 'updated_on' fields
        are always read only.
        """
        if obj is not None:
            return self.readonly_fields + \
                ('created_by', 'created_on', 'updated_on')

        return self.readonly_fields

    def get_actions(self, request):
        """
        override :meth:`django.contrib.admin.ModelAdmin.get_actions`

        The purpose is to only allow superusers the privilege of deleting
        objects from `Django Admin Summary pages`
        """
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']

        return actions

    def save_model(self, request, obj, form, change):
        """
        override :meth:`django.contrib.admin.ModelAdmin.save_model`

        pre-populates created_by and updated_by fields. created_by must only
        be updated once  upon creation
        """
        if not hasattr(obj, 'created_by'):
            obj.created_by = request.user

        obj.updated_by = request.user

        obj.save()
