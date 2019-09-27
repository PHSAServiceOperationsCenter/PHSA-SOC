"""
.. _base_admin:

:module:    p_soc_auto.p_soc_auto_base.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    sep. 17, 2018

`django.contrib.admin` objects to be reused across the :ref:`SOC Automation
Server` apps

"""
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import FieldDoesNotExist


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
