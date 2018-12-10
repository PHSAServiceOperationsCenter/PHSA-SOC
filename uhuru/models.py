"""
.. _models:

django models module for the uhuru app

:module:    uhuru.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Dec. 10, 2018

"""
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from phonenumber_field.modelfields import PhoneNumberField

from p_soc_auto_base.models import BaseModel

EMAIL_TEMPLATE_PATH = os.path.join(settings.BASE_DIR, 'uhuru/templates/email')


class Subscriber(BaseModel, models.Model):
    subscriber = models.OneToOneField(
        get_user_model(), db_index=True, blank=False, null=False,
        on_delete=models.CASCADE)
    delegate = models.ManyToManyField(
        'self', symmetrical=False, through='Delegation',
        verbose_name=_('Delegate to'), related_name='delegate_to')
    escalate = models.ManyToManyField(
        'self', symmetrical=False, through='Escalation',
        verbose_name=_('Escalate to'), related_name='escalate_to')

    def __str__(self):
        return '{} {}'.format(self.subscriber.first_name,
                              self.subscriber.last_name)

    class Meta:
        app_label = 'uhuru'
        verbose_name = _('Subscriber')
        verbose_name_plural = _('Subscribers')


class SubscriberGroup(BaseModel, models.Model):
    subscriber_group = models.CharField(
        _('subscriber group name'), unique=True, db_index=True, blank=False,
        null=False, max_length=64)
    subscriber = models.ManyToManyField(
        Subscriber, db_index=True, verbose_name=_('Team Member'))
    group_email_address = models.EmailField(
        _('group email address'), db_index=True, blank=True, null=True)
    group_pager = PhoneNumberField(
        _('group pager telephone number'), db_index=True, blank=True,
        null=True)

    def __str__(self):
        return self.subscriber_group

    class Meta:
        app_label = 'uhuru'
        verbose_name = _('Subscriber Group')
        verbose_name_plural = _('Subscriber Groups')


class Delegation(BaseModel, models.Model):
    subscriber = models.ForeignKey(
        Subscriber, db_index=True, blank=False, null=False,
        verbose_name=_('Team Member'), on_delete=models.CASCADE,
        related_name='delegate_from_subscriber')
    delegate_to = models.ForeignKey(
        Subscriber, db_index=True, blank=False, null=False,
        verbose_name=_('Delegate to Team Member'), on_delete=models.CASCADE,
        related_name='delegate_to_subscriber')
    enabled = models.BooleanField(
        _('enabled'), db_index=True, default=False, null=False, blank=False,
        help_text=_('if this field is checked out, the row will always be'
                    ' excluded from any active operation'))

    def __str__(self):
        return 'Notifications for {} will be delegated to {}'.\
            format(self.subscriber, self.delegate_to)

    class Meta:
        app_label = 'uhuru'
        verbose_name = _('Delegation')
        verbose_name_plural = _('Delegations')


class Escalation(BaseModel, models.Model):
    subscriber = models.ForeignKey(
        Subscriber, db_index=True, blank=False, null=False,
        verbose_name=_('Team Member'), on_delete=models.CASCADE,
        related_name='escalate_from_subscriber')
    escalate_to = models.ForeignKey(
        Subscriber, db_index=True, blank=False, null=False,
        verbose_name=_('Escalate to Team Member'), on_delete=models.CASCADE,
        related_name='escalate_to_subscriber')

    def __str__(self):
        return 'Notifications for {} will be escalated to {}'.\
            format(self.subscriber, self.escalate_to)

    class Meta:
        app_label = 'uhuru'
        verbose_name = _('Escalation')
        verbose_name_plural = _('Escalations')


class EmailAddress(BaseModel, models.Model):
    subscriber = models.ForeignKey(
        Subscriber, db_index=True, blank=False, null=False,
        on_delete=models.CASCADE, verbose_name=_('subscriber'))
    email_address = models.EmailField(
        _('email address'), unique=True, db_index=True, blank=False,
        null=False)

    def __str__(self):
        return '%s %s <%s>' % (self.subscriber.first_name,
                               self.subscriber.last_name,
                               self.email_address)

    class Meta:
        verbose_name = _('Email Address')
        verbose_name_plural = _('Email Addresses')
        app_label = 'uhuru'


class Telephone(BaseModel, models.Model):
    subscriber = models.ForeignKey(
        Subscriber, db_index=True, blank=False, null=False,
        on_delete=models.CASCADE, verbose_name=_('subscriber'))
    telephone = PhoneNumberField(
        _('telephone'), unique=True, db_index=True, blank=False, null=False)
    is_sms = models.BooleanField(
        _('SMS capable'), db_index=True, default=True, null=False, blank=False,
        help_text=_('this is a pager or SMS capable telephone number'))

    def __str__(self):
        return '{} {}: {}'.\
            format(self.subscriber.first_name,
                   self.subscriber.last_name, self.telephone)

    class Meta:
        app_label = 'uhuru'
        verbose_name = _('Phone Number')
        verbose_name_plural = _('Phone Numbers')


class Subject(BaseModel, models.Model):
    subject = models.CharField(
        _('subject'), max_length=253, unique=True, db_index=True, blank=False,
        null=False)
    originating_email = models.EmailField(
        _('from email address'), db_index=True, blank=False, null=False,
        default=settings.DEFAULT_FROM_EMAIL)
    template_file = models.FilePathField(
        _('template file'), path=EMAIL_TEMPLATE_PATH,
        match=r'.*\.email$',
        allow_files=True, recursive=False, max_length=253, blank=False,
        null=False, db_index=True)
    subscribers = models.ManyToManyField(
        Subscriber, through='UserSubscription',
        verbose_name=_('users subscribing to this subject'))
    subscribing_groups = models.ManyToManyField(
        SubscriberGroup, through='GroupSubscription',
        verbose_name=_('groups subscribing to this subject'))

    def __str__(self):
        return self.subject

    class Meta:
        app_label = 'uhuru'
        verbose_name = _('Subscription Subject')
        verbose_name_plural = _('Subscription Subjects')


class SubjectHeader(BaseModel, models.Model):
    subject_header = models.CharField(
        _('subject header'), max_length=64, unique=True, db_index=True,
        blank=False, null=False)
    subject = models.ForeignKey(
        Subject, db_index=True, null=False, blank=False,
        on_delete=models.CASCADE, verbose_name=_('subject'))

    def __str__(self):
        return '{}.{}'.format(self.subject.subject, self.subject_header)

    class Meta:
        app_label = 'uhuru'
        verbose_name = _('Subject Header')
        verbose_name_plural = _('Subject Headers')


class SubjectTag(BaseModel, models.Model):
    subject_tag = models.CharField(
        _('tag'), max_length=64, unique=True, db_index=True,
        blank=False, null=False)
    subject = models.ForeignKey(
        Subject, db_index=True, null=False, blank=False,
        on_delete=models.CASCADE, verbose_name=_('subject'))

    def __str__(self):
        return '[{}] {}'.format(self.subject_tag, self.subject.subject)

    class Meta:
        app_label = 'uhuru'
        verbose_name = _('Subject Tag')
        verbose_name_plural = _('Subject Tags')
        indexes = [models.Index(fields=['subject_tag', 'subject']), ]


class UserSubscription(BaseModel, models.Model):
    subject = models.ForeignKey(
        Subject, db_index=True, blank=False, null=False,
        on_delete=models.CASCADE, verbose_name=_('subscribes to'))
    subscriber = models.ForeignKey(
        Subscriber, db_index=True, blank=False, null=False,
        on_delete=models.CASCADE, verbose_name=_('subscriber'))

    def __str__(self):
        return '{} is receiving notifications about {}'.format(
            self.subscriber, self.subject)

    class Meta:
        app_label = 'uhuru'
        indexes = [models.Index(fields=['subject', 'subscriber', ]), ]
        unique_together = (('subject', 'subscriber', ), )
        verbose_name = _("User's Subscriptions")
        verbose_name_plural = _("Users' Subscriptions")


class GroupSubscription(BaseModel, models.Model):
    subject = models.ForeignKey(
        Subject, db_index=True, blank=False, null=False,
        on_delete=models.CASCADE, verbose_name=_('subscribes to'))
    subscribing_group = models.ForeignKey(
        SubscriberGroup, db_index=True, blank=False, null=False,
        on_delete=models.CASCADE, verbose_name=_('subscribing group'))

    def __str__(self):
        return '{} is receiving notifications about {}'.format(
            self.subscribing_group, self.subject)

    class Meta:
        app_label = 'uhuru'
        indexes = [models.Index(fields=['subject', 'subscribing_group', ]), ]
        unique_together = (('subject', 'subscribing_group', ), )
        verbose_name = _("Group's Subscriptions")
        verbose_name_plural = _("Groups' Subscriptions")
