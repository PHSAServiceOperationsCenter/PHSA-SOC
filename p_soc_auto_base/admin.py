"""
.. _admin:

django admin for the p_soc_aut_base app

contains base classes for admin forms

:module:    p_soc_auto.p_soc_auto_base.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    sep. 17, 2018
"""
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import FieldDoesNotExist


def enable_selected(modeladmin, request, queryset):
    """
    enable objects admin action
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
    disable objects admin action
    """
    try:
        modeladmin.model._meta.get_field('enabled')
    except FieldDoesNotExist as err:
        modeladmin.message_user(request, str(err), level=messages.ERROR)
        return

    rows_enabled = queryset.update(enabled=True)
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
    base class for admin classes
    """
    actions_on_top = True
    actions_on_bottom = True
    actions_selection_counter = True
    save_on_top = True

    def get_actions(self, request):
        """
        make the delete selected action available if the user is a superuser
        """
        actions = super().get_actions(request)
        if not request.user.is_superuser:
            if 'delete_selected' in actions:
                del actions['delete_selected']

        return actions
