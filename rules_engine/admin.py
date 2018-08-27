from django.contrib import admin

from .models import (
    TinDataForRuleDemos, IntervalRule, RuleApplies, ExpirationRule,
    NotificationEventForRuleDemo)


@admin.register(TinDataForRuleDemos)
class TinDataAdmin(admin.ModelAdmin):
    list_display = ('data_name', 'data_datetime_1', 'data_number_1',
                    'data_string_1', 'data_datetime_2', 'data_number_2',
                    'data_string_2')
    list_editable = ('data_datetime_1', 'data_number_1',
                     'data_string_1', 'data_datetime_2', 'data_number_2',
                     'data_string_2')


@admin.register(IntervalRule)
class IntervalRuleAdmin(admin.ModelAdmin):
    list_display = ('rule', 'min_val', 'max_val')
    list_editable = ('min_val', 'max_val')


@admin.register(ExpirationRule)
class ExpirationRuleAdmin(admin.ModelAdmin):
    list_display = ('rule', 'valid_after', 'grace_period')
    list_editable = ('valid_after', 'grace_period')


@admin.register(RuleApplies)
class RuleAppliesAdmin(admin.ModelAdmin):
    list_display_links = ('id',)
    list_display = ('id', 'rule', 'content_type')
    list_editable = ('rule', 'content_type')


@admin.register(NotificationEventForRuleDemo)
class NotificationEventForRuleDemoAdmin(admin.ModelAdmin):
    list_display = ('notification', 'notification_level', 'notification_type',
                    'notification_args')
