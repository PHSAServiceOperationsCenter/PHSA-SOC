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
import uuid
import json

from decimal import Decimal

from dateutil import parser as datetime_parser

from django.db import models
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from jsonfield import JSONField

from p_soc_auto_base.models import BaseModel
from notifications.models import (
    Notification, NotificationLevel, NotificationType,
)


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

    class Meta:
        verbose_name = 'Sample data for demonstrating rules'
        verbose_name_plural = 'Sample data for demonstrating rules'


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

    class Meta:
        verbose_name = 'Place holder for notifications'
        verbose_name_plural = 'Place holder for notifications'


class Rule(BaseModel, models.Model):
    """
    base rule class
    """
    rule = models.CharField(
        _('rule name'), max_length=253, db_index=True, unique=True,
        blank=False, null=False,
        help_text=_('mother of inventions'))
    applies = models.ManyToManyField(
        ContentType, through='RuleApplies',
        verbose_name=_('This Rule Applies to'))
    subscribers = models.TextField(
        _('rule subscribers'), blank=True, null=True,
        help_text=_('send notifications raised by this rule to these users.'
                    ' this will be replaced by a reference once a'
                    ' subscriptions application becomes available'))
    escalation_subscribers = models.TextField(
        _('rule escalation subscribers'), blank=True, null=True,
        help_text=_('send escalation notifications raised by this rule to'
                    ' these users.'
                    ' this will be replaced by a reference once a'
                    ' subscriptions application becomes available'))

    def raise_rule_notification(
            self, rule_applies=None, rule_msg=None, instance_pk=None):
        """
        raise a notification based on a rule triggered event

        :arg rule_applies: the instance of the of the :class:`RuleApplies`

            this object will give access to all the pertinent information
            for the rule that was triggered:

            * the rule itself
            * the content_type to which the rule is applied (via
              :class:`django.contrib.contenttypes.models.ContentType`
            * the field to which the rule is applied

        :arg rule_msg: a `json` representation of the fact used to trigger
                       the rule

            this data structure needs to include the (value of the) fact, the
            rule data points, and the relationship between the fact and the
            data points.

            for example, an interval rule will be represented as
            {'fact': fact_value, 'relationship': 'between',
             'initial_value': value, 'interval': interval}

        :arg int instance_pk: the instance pk for the object that caused the
                              rule event
        """
        if rule_applies is None:
            raise NotificationError(
                'cannot raise notification without a causing rule')
        if not isinstance(rule_applies, RuleApplies):
            raise NotificationError(
                'trying to raise notification without a rule if not allowed')

        if rule_msg is None:
            raise NotificationError(
                'cannot raise notification without providing an explanation')

        if instance_pk is None:
            raise NotificationError(
                'cannot raise notification without an object to which the'
                ' notification applies')

        notification = Notification(notification_uuid=uuid.uuid4())

        notification.created_by = self.get_or_create_user(
            username=settings.RULES_ENGINE_SERVICE_USER)
        notification.updated_by = self.get_or_create_user(
            username=settings.RULES_ENGINE_SERVICE_USER)
        notification.rule_applies = rule_applies
        notification.notification_type = rule_applies.notification_type
        notification.notification_level = rule_applies.notification_level
        notification.rule_msg = rule_msg
        notification.instance_pk = instance_pk

        notification.save()

    def raise_admin_notification(self, rule_applies):
        """
        raise a notification when a rule apply operation fails because there
        is not qualifying content

        this happens if the rule_applies object was defined against a data
        model that doesn't exist anymore
        """
        notification = Notification(notification_uuid=uuid.uuid4())

        notification.created_by = self.get_or_create_user(
            username=settings.RULES_ENGINE_SERVICE_USER)
        notification.updated_by = self.get_or_create_user(
            username=settings.RULES_ENGINE_SERVICE_USER)
        notification.rule_applies = rule_applies
        notification.notification_type = NotificationType.objects.\
            get(notification_type='internal')
        notification.notification_level = NotificationLevel.objects.\
            get(notification_level='ADMINISTRATIVE')
        notification.rule_msg = json.dumps(
            dict(rule=rule_applies.rule.rule,
                 relationship='is missing',
                 data=rule_applies.content_type.name)
        )

        notification.save()

    def raise_bad_rule_notification(self, rule_applies, rule_msg, instance_pk):
        """
        raise a notification if the rule evaluation raises some sort of
        exception. for example, the fact is of a type different than the data

        """
        notification = Notification(notification_uuid=uuid.uuid4())

        notification.created_by = self.get_or_create_user(
            username=settings.RULES_ENGINE_SERVICE_USER)
        notification.updated_by = self.get_or_create_user(
            username=settings.RULES_ENGINE_SERVICE_USER)
        notification.rule_applies = rule_applies
        notification.notification_type = NotificationType.objects.\
            get(notification_type='internal')
        notification.notification_level = NotificationLevel.objects.\
            get(notification_level='INVALID_RULE')
        notification.rule_msg = rule_msg
        notification.instance_pk = instance_pk

        notification.save()

    def apply_rule(self):
        """
        just a place holder. this method needs to exist in child classes
        """
        raise NotImplementedError('must be implemented in the subclass')

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
                self.raise_admin_notification(rule_applies)
                continue

            for obj in queryset:
                try:
                    fact = str(rule_applies.get_fact_for_field(obj))
                except Exception as err:
                    rule_msg = dict(fact='undefined',
                                    relationship='throws',
                                    exception_type=type(err),
                                    exception_msg=str(err))
                    self.raise_bad_rule_notification(
                        rule_applies=rule_applies,
                        rule_msg=json.dumps(rule_msg), instance_pk=obj.pk)

                if re_find.search(fact):
                    rule_msg = dict(fact=fact, relationship='contains',
                                    match_string=self.match_string)
                    self.raise_rule_notification(
                        rule_applies=rule_applies,
                        rule_msg=json.dumps(rule_msg), instance_pk=obj.pk)

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
                self.raise_admin_notification(rule_applies)
                continue

            for obj in queryset:
                try:
                    fact = Decimal(rule_applies.get_fact_for_field(obj))
                    if not fact.is_finite():
                        rule_msg = dict(fact=fact,
                                        relationship='outside domain',
                                        min_val=self.min_val,
                                        max_val=self.min_val + self.interval)
                        self.raise_bad_rule_notification(
                            rule_applies=rule_applies,
                            rule_msg=json.dumps(rule_msg), instance_pk=obj.pk)
                except Exception as err:
                    rule_msg = dict(fact='undefined',
                                    relationship='throws',
                                    exception_type=type(err),
                                    exception_msg=str(err))
                    self.raise_bad_rule_notification(
                        rule_applies=rule_applies,
                        rule_msg=json.dumps(rule_msg), instance_pk=obj.pk)

                if not self.min_val <= fact <= self.min_val + self.interval:
                    rule_msg = dict(fact=fact,
                                    relationship='not between',
                                    min_val=self.min_val,
                                    max_val=self.min_val + self.interval)
                    self.raise_rule_notification(
                        rule_applies=rule_applies,
                        rule_msg=json.dumps(rule_msg), instance_pk=obj.pk)

    class Meta:
        app_label = 'rules_engine'
        verbose_name = _('Interval Rule')
        verbose_name_plural = _('Interval Rules')


class ExpirationRule(Rule, models.Model):
    """
    notify if fact is datetime and falls within now() + timedelta

    fact is not between valid_after and now() + grace_period
    """
    grace_period = models.DurationField('grace_period')

    def apply_rule(self):
        for rule_applies in RuleApplies.objects.filter(rule=self):
            try:
                queryset = rule_applies.\
                    content_type.get_all_objects_for_this_type()
            except Exception as err:
                self.raise_admin_notification(rule_applies)
                continue

            for obj in queryset:
                try:
                    facts = rule_applies.get_facts_for_fields(obj)
                    if not isinstance(facts, list):
                        rule_msg = dict(fact=facts,
                                        relationship='not enough facts')
                        self.raise_bad_rule_notification(
                            rule_applies=rule_applies,
                            rule_msg=json.dumps(rule_msg), instance_pk=obj.pk)
                        continue
                    for fact in facts:
                        if not isinstance(fact, datetime.datetime):
                            fact = datetime_parser.parse(fact)
                except Exception as err:
                    rule_msg = dict(fact=facts,
                                    relationship='throws',
                                    # exception_type=type(err),
                                    exception_msg=str(err))
                    self.raise_bad_rule_notification(
                        rule_applies=rule_applies,
                        rule_msg=json.dumps(rule_msg), instance_pk=obj.pk)

                now = timezone.now()
                rule_msg = dict(facts=facts, now=now,
                                grace_period=self.grace_period)

                if now < facts[0]:
                    rule_msg['relationship'] = 'not yet valid'
                elif facts[1] - self.grace_period <= now <= facts[1]:
                    rule_msg['relationship'] = (
                        'will expire in less than %s' % self.grace_period)
                elif facts[1] < now:
                    rule_msg['relationship'] = 'has expired'

                self.raise_notification(
                    rule_applies=rule_applies,
                    rule_msg=json.dumps(rule_msg), instance_pk=obj.pk)

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
        ContentType, on_delete=models.CASCADE, blank=False, null=False,
        verbose_name=_('Content Type'),
        help_text=_('Links a rule to a model to which the rule applies to'))
    field_name = models.CharField(
        _('field name'), max_length=64, db_index=True, blank=False, null=False,
        help_text=_('the name of the field where the rule fact resides'))
    second_field_name = models.CharField(
        _('second field name'), max_length=64, db_index=True, blank=True,
        null=True,
        help_text=_(
            'the name of the field where the second rule fact resides'))
    subscribers = models.TextField(
        _('model-field subscribers'), blank=True, null=True,
        help_text=_('send notifications raised when applying this rule to'
                    ' this particular model-field combination to these users.'
                    ' this will be replaced by a reference once a'
                    ' subscriptions application becomes available'))
    escalation_subscribers = models.TextField(
        _('model-field escalation subscribers'), blank=True, null=True,
        help_text=_('send escalated notifications raised when applying this'
                    ' rule to'
                    ' this particular model-field combination to these users.'
                    ' this will be replaced by a reference once a'
                    ' subscriptions application becomes available'))
    notification_type = models.ForeignKey(
        'notifications.NotificationType', on_delete=models.PROTECT,
        db_index=True,
        blank=True, null=True, verbose_name=_('Notification Type'))
    notification_level = models.ForeignKey(
        'notifications.NotificationLevel', on_delete=models.PROTECT,
        db_index=True,
        blank=True, null=True, verbose_name=_('Notification Level'))

    def __str__(self):
        if self.second_field_name is None:
            fields = 'field %s' % self.field_name
        else:
            fields = 'fields %s' % ', '.join(
                [self.field_name, self.second_field_name])

        return ('apply rule %s against %s of model %s' %
                (self.rule.rule, fields, self.content_type.model))

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

    def get_facts_for_fields(self, obj):
        """
        support getting facts from two fields
        """
        if self.second_field_name is None:
            return self.get_fact_for_field(obj)

        return [getattr(self.content_type.get_object_for_this_type(pk=obj.id),
                        self.field_name),
                getattr(self.content_type.get_object_for_this_type(pk=obj.id),
                        self.field_name)]

    class Meta:
        verbose_name = _('Content to which a Rule Applies')
        verbose_name_plural = _('Content to which a Rule Applies')
        unique_together = (('rule', 'content_type', 'field_name'))
