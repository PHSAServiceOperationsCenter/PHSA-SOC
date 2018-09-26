"""
.. _admin:

django admin for the rules_engine app

:module:    p_soc_auto.rules_engine.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    sep. 18, 2018
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType

from p_soc_auto_base.admin import BaseAdmin

from .models import (
    TinDataForRuleDemos, IntervalRule, RuleApplies, ExpirationRule,
    NotificationEventForRuleDemo, RegexRule)
from .forms import RuleAppliesForm


class RulesEngineBaseAdmin(BaseAdmin, admin.ModelAdmin):
    """
    base admin class for this application
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

        if db_field.name in ['content_type', ]:
            kwargs['queryset'] = ContentType.objects.\
                filter(app_label__in=[
                    'orion_integration', 'rules_engine', 'ssl_cert_tracker',
                    'notifications'])

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


class RuleAppliesInlineAdmin(admin.TabularInline):
    """
    inline form for rule_applies manytomany
    """
    form = RuleAppliesForm
    model = RuleApplies
    fields = ('enabled', 'content_type',
              'field_name', 'get_current_field_name',
              'second_field_name', 'get_current_second_field_name',
              'updated_by',)
    readonly_fields = ('get_current_field_name',
                       'get_current_second_field_name',)
    extra = 0
    max_num = 0
    show_change_link = True

    def get_current_field_name(self, obj):
        return obj.field_name
    get_current_field_name.short_description = 'current value for field name'

    def get_current_second_field_name(self, obj):
        return obj.second_field_name
    get_current_second_field_name.short_description = \
        'current value for second field name'

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

        if db_field.name in ['content_type', ]:
            kwargs['queryset'] = ContentType.objects.\
                filter(app_label__in=[
                    'orion_integration', 'rules_engine', 'ssl_cert_tracker',
                    'notifications'])

        return super().formfield_for_foreignkey(db_field, request, **kwargs)


@admin.register(TinDataForRuleDemos)
class TinDataAdmin(admin.ModelAdmin):
    """
    admin class for the demo data model
    """
    list_display = ('data_name', 'data_datetime_1', 'data_number_1',
                    'data_string_1', 'data_datetime_2', 'data_number_2',
                    'data_string_2', 'created_by',
                    'updated_by', 'created_on', 'updated_on')
    list_editable = ('data_datetime_1', 'data_number_1',
                     'data_string_1', 'data_datetime_2', 'data_number_2',
                     'data_string_2')
    search_fields = ['data_name', ]


@admin.register(IntervalRule)
class IntervalRuleAdmin(RulesEngineBaseAdmin, admin.ModelAdmin):
    """
    admin class for creating interval based rules
    """
    list_display = ('rule', 'min_val', 'interval', 'created_by',
                    'updated_by', 'created_on', 'updated_on')
    list_editable = ('min_val', 'interval')
    search_fields = ['rule', ]

    inlines = [RuleAppliesInlineAdmin, ]


@admin.register(ExpirationRule)
class ExpirationRuleAdmin(RulesEngineBaseAdmin, admin.ModelAdmin):
    """
    admin class for creating expiration based rules
    """
    list_display = ('rule', 'grace_period', 'created_by',
                    'updated_by', 'created_on', 'updated_on')
    list_editable = ('grace_period',)
    search_fields = ['rule', ]

    inlines = [RuleAppliesInlineAdmin, ]


@admin.register(RuleApplies)
class RuleAppliesAdmin(RulesEngineBaseAdmin, admin.ModelAdmin):
    """
    admin class fro linking rules to objects
    """
    form = RuleAppliesForm

    readonly_fields = ('get_current_field_name',
                       'get_current_second_field_name',
                       'created_on', 'updated_on')
    list_display_links = ('id',)
    list_display = ('id', 'rule', 'content_type', 'field_name',
                    'second_field_name', 'created_by',
                    'created_on', 'updated_by', 'updated_on')
    list_editable = ('rule', 'content_type',)

    def get_current_field_name(self, obj):
        return obj.field_name
    get_current_field_name.short_description = 'current value for field name'

    def get_current_second_field_name(self, obj):
        return obj.second_field_name
    get_current_second_field_name.short_description = \
        'current value for second field name'


@admin.register(NotificationEventForRuleDemo)
class NotificationEventForRuleDemoAdmin(admin.ModelAdmin):
    list_display = ('notification', 'notification_level', 'notification_type',
                    'notification_args')


@admin.register(RegexRule)
class RegexRuleAdmin(RulesEngineBaseAdmin, admin.ModelAdmin):
    list_display = ('rule', 'match_string', 'created_by',
                    'updated_by', 'created_on', 'updated_on')
    list_editable = ('match_string',)
    search_fields = ['rule', ]

    inlines = [RuleAppliesInlineAdmin, ]
