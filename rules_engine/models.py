"""
.. _models:

django models for the rules_engine app

:module:    p_soc_auto.rules_engine.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

"""
import collections
import datetime
import re

from decimal import Decimal

from dateutil import parser as datetime_parser

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from jsonfield import JSONField

from p_soc_auto_base.models import BaseModel


class NotificationError(Exception):
    """
    raise if there is an error in creating the notification record
    """
    pass


class TinDataForRuleDemos(BaseModel, models.Model):
    """
    just a test class to screw around; will go away soon
    """
    data_name = models.CharField(
        'data_name', max_length=64, db_index=True, unique=True, blank=False,
        null=False)
    data_datetime_1 = models.DateTimeField('data_datetime_1')
    data_number_1 = models.IntegerField('data_number_1')
    data_string_1 = models.CharField('data_string_1', max_length=16)
    data_datetime_2 = models.DateTimeField('data_datetime_2')
    data_number_2 = models.IntegerField('data_number_2')
    data_string_2 = models.CharField('data_string_2', max_length=16)

    def __str__(self):
        return self.data_name


class NotificationEventForRuleDemo(BaseModel, models.Model):
    """
    fake notification class
    will create something more sophisticated when implementing
    notifications
    """
    notification = models.CharField(
        'notification', max_length=253, db_index=True, unique=True,
        blank=False, null=False)
    notification_level = models.CharField(
        'log, info, warn, error, critical, kill me now', max_length=64,
        default='info')
    notification_type = models.CharField(
        'log, notify, notify and escalate, etc', max_length=64,
        default='notify')
    notification_args = JSONField(
        load_kwargs={'object_pairs_hook': collections.OrderedDict})

    def __str__(self):
        return self.notification


class Rule(BaseModel, models.Model):
    """
    base rule class
    """
    rule = models.CharField(
        _('rule name'), max_length=253, db_index=True, unique=True,
        blank=False, null=False,
        help_text=_('mother of inventions'))
    applies = models.ManyToManyField(
        ContentType, through='RuleApplies')

    def raise_notification(
            self, notification_type=None, notification_notes=None, **kwargs):
        """
        raise a notification

        currently this just creates a record in the notification table
        """
        if notification_type is None:
            raise NotificationError('must specify a notification type')

        notification = NotificationEventForRuleDemo(
            notification='%s: notify from %s' % (timezone.now(), self.rule),
            notification_type=notification_type, notes=notification_notes)
        notification.notification_args = dict(**kwargs)
        notification.created_by_id = 1
        notification.updated_by_id = 1
        notification.save()

    def apply_rule(self):
        pass

    def __str__(self):
        return self.rule

    class Meta:
        app_label = 'rules_engine'
        verbose_name = _('Basic Rule')
        verbose_name_plural = _('Basic Rules')


class RegexRule(Rule, models.Model):
    """
    rules of type 'is string in fact'

    useful for looking for specific messages in log files
    """
    match_string = models.CharField(
        _('raise when matching'), max_length=253, db_index=True, blank=False,
        null=False)

    def apply_rule(self):
        """
        apply this rule to all registered content_type, field_name combinations
        """
        re_find = re.compile(self.match_string, flags=re.I | re.M)
        for rule_applies in RuleApplies.objects.filter(rule=self):
            try:
                queryset = rule_applies.\
                    content_type.get_all_objects_for_this_type()
            except Exception as err:
                self.raise_notification(
                    notification_type='administrative',
                    notification_note='%s does not exist. error: %s'
                    % (rule_applies.content_type.name, str(err)))
                continue

            for obj in queryset:
                try:
                    fact = str(rule_applies.get_fact_for_field(obj))
                except Exception as err:
                    self.raise_notification(
                        notification_type='invalid rule',
                        model=rule_applies.content_type.name,
                        field=rule_applies.field_name,
                        expected=self.match_string,
                        value=fact, notification_note=str(err))

                if re_find.search(fact):
                    self.raise_notification(
                        notification_type=self._meta.verbose_name,
                        model=rule_applies.content_type.name,
                        field=rule_applies.field_name,
                        value=fact, match=self.match_string)

    class Meta:
        app_label = 'rules_engine'
        verbose_name = _('String Match Rule')
        verbose_name_plural = _('String Match Rules')


class IntervalRule(Rule, models.Model):
    """
    class for interval based rules

    run the action if the fact is a number and it is not contained in the
    interval defined by :var:`min_val` and :var:`interval`
    """
    interval = models.DecimalField(
        _('interval'), max_digits=5, decimal_places=2,
        default=Decimal('000.00'))
    min_val = models.DecimalField(
        _('minimum acceptable value'), max_digits=5, decimal_places=2,
        default=Decimal('100.00'))

    def apply_rule(self):
        """
        apply this rule to all the content_type, field_name combinations
        associated with it
        """
        for rule_applies in RuleApplies.objects.filter(rule=self):
            try:
                queryset = rule_applies.\
                    content_type.get_all_objects_for_this_type()
            except Exception as err:
                self.raise_notification(
                    notification_type='administrative',
                    notification_note='%s does not exist. error: %s'
                    % (rule_applies.content_type.name, str(err)))
                continue

            for obj in queryset:
                try:
                    fact = Decimal(rule_applies.get_fact_for_field(obj))
                    if not fact.is_finite():
                        self.raise_notification(
                            notification_type='invalid rule',
                            notification_note=(
                                'was looking for something between %s and %s'
                                % (str(self.min_val),
                                   str(self.min_val + self.interval))),
                            model=rule_applies.content_type.name,
                            field=rule_applies.field_name,
                            value=fact, critical='not a number')
                except Exception as err:
                    self.raise_notification(
                        notification_type='invalid rule',
                        notification_note=(
                            'was looking for something between %s and %s'
                            % (str(self.min_val),
                               str(self.min_val + self.interval))),
                        model=rule_applies.content_type.name,
                        field=rule_applies.field_name,
                        value=fact, critical=str(err))

                if not self.min_val <= fact <= self.min_val + self.interval:
                    self.raise_notification(
                        notification_type=self._meta.verbose_name,
                        model=rule_applies.content_type.name,
                        field=rule_applies.field_name,
                        value=fact,
                        min_val=self.min_val,
                        max_val=self.min_val + self.interval)

    class Meta:
        app_label = 'rules_engine'
        verbose_name = _('Interval Rule')
        verbose_name_plural = _('Interval Rules')


class ExpirationRule(Rule, models.Model):
    """
    notify if fact is datetime and falls within now() + timedelta

    fact is not between valid_after and now() + grace_period
    """
    valid_after = models.DateTimeField('valid_after')
    grace_period = models.DurationField('grace_period')

    def apply_rule(self):
        for rule_applies in RuleApplies.objects.filter(rule=self):
            try:
                queryset = rule_applies.\
                    content_type.get_all_objects_for_this_type()
            except Exception as err:
                self.raise_notification(
                    notification_type='administrative',
                    notification_note='%s does not exist. error: %s'
                    % (rule_applies.content_type.name, str(err)))
                continue

            for obj in queryset:
                try:
                    fact = rule_applies.get_fact_for_field(obj)
                    if not isinstance(fact, datetime.datetime):
                        fact = datetime_parser.parse(fact)
                except Exception as err:
                    self.raise_notification(
                        notification_type='invalid rule',
                        notification_note=(
                            'was looking for something between %s and %s'
                            % (str(self.valid_after),
                               str(timezone.now() + self.grace_period))),
                        model=rule_applies.content_type.name,
                        field=rule_applies.field_name,
                        value=fact, critical=str(err))

                if not self.valid_after <= fact <= timezone.now() \
                        + self.grace_period:
                    self.raise_notification(
                        notification_type=self._meta.verbose_name,
                        model=rule_applies.content_type.name,
                        field=rule_applies.field_name,
                        value=fact,
                        valid_after=self.valid_after,
                        expire_in_less_than=self.grace_period)

    class Meta:
        app_label = 'rules_engine'
        verbose_name = _('Certificate Validity Rule')
        verbose_name_plural = _('Certificate Validity Rules')


class RuleApplies(BaseModel, models.Model):
    """
    relate a rule to the model and field against which it is to be applied

    code would look somewhat like this

    for rule in Rule.objects.all():
        for applies in rule.applies.all():
            for obj in applies.content_type.objects.all():
                rule.apply()

    """
    rule = models.ForeignKey(
        Rule, on_delete=models.CASCADE, blank=False, null=False,
        verbose_name=_('Rule'))
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE)
    field_name = models.CharField('field', max_length=64)

    def get_fact_for_field(self, obj):
        """
        :returns:
            the value of the field identified by :var:`field_name
            in the model instance defined by :var:`content_type`.
            this the equivalent of the fact in an in inference engine
        """
        return getattr(
            self.content_type.get_object_for_this_type(pk=obj.id),
            self.field_name)
