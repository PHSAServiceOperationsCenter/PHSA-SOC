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

from .models import (
    TinDataForRuleDemos, IntervalRule, RuleApplies, ExpirationRule,
    NotificationEventForRuleDemo, RegexRule)


@admin.register(TinDataForRuleDemos)
class TinDataAdmin(admin.ModelAdmin):
    """
    admin class for the demo data model
    """
    list_display = ('data_name', 'data_datetime_1', 'data_number_1',
                    'data_string_1', 'data_datetime_2', 'data_number_2',
                    'data_string_2')
    list_editable = ('data_datetime_1', 'data_number_1',
                     'data_string_1', 'data_datetime_2', 'data_number_2',
                     'data_string_2')
    search_fields = ['data_name', ]


@admin.register(IntervalRule)
class IntervalRuleAdmin(admin.ModelAdmin):
    """
    admin class for creating interval based rules
    """
    list_display = ('rule', 'min_val', 'interval')
    list_editable = ('min_val', 'interval')


@admin.register(ExpirationRule)
class ExpirationRuleAdmin(admin.ModelAdmin):
    """
    admin class for creating expiration based rules
    """
    list_display = ('rule', 'valid_after', 'grace_period')
    list_editable = ('valid_after', 'grace_period')


@admin.register(RuleApplies)
class RuleAppliesAdmin(admin.ModelAdmin):
    """
    admin class fro linking rules to objects
    """
    list_display_links = ('id',)
    list_display = ('id', 'rule', 'content_type', 'field_name', 'created_by',
                    'created_on', 'updated_by', 'updated_on')
    list_editable = ('rule', 'content_type', 'field_name')


@admin.register(NotificationEventForRuleDemo)
class NotificationEventForRuleDemoAdmin(admin.ModelAdmin):
    list_display = ('notification', 'notification_level', 'notification_type',
                    'notification_args')


@admin.register(RegexRule)
class RegexRuleAdmin(admin.ModelAdmin):
    list_display = ('rule', 'match_string')
    list_editable = ('match_string',)
