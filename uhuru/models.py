"""
.. _models:

django models module for the uhuru app

:module:    uhuru.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Nov. 23, 2018

"""
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import models

from p_soc_auto_base.models import BaseModel


class Subscriber(BaseModel, models.Model):
    subscriber = models.OneToOneField(
        get_user_model(), db_index=True, blank=False, null=False)
    partner = models.ManyToManyField(
        'self', symmetrical=False, through='Team',
        verbose_name=_('Delegation and Escalation'))

    def __str__(self):
        return '%s %s' % (self.subscriber.first_name,
                          self.subscriber.last_name)

    class Meta:
        app_label = 'uhuru'
        verbose_name = _('Subscriber')
        verbose_name_plural = _('Subscribers')


class Team(BaseModel, models.Model):
    subscriber = models.ForeignKey(
        Subscriber, db_index=True, blank=False, null=False,
        verbose_name=_('Team Member'), on_delete=models.CASCADE)
    partner = models.ForeignKey(
        Subscriber, db_index=True, blank=False, null=False,
        verbose_name=_('Team Partner'), on_delete=models.CASCADE)
    delegate = models.BooleanField(
        _('Delegate To'), db_index=True, blank=False, null=False,
        default=False, help_text=_(
            'email for the subscriber will be forwarded to the partner'
            ' if delegate is enabled'))
    escalate = models.BooleanField(
        _('Escalate To'), db_index=True, blank=False, null=False,
        default=False, help_text=_(
            'email for the subscriber will be forwarded to the partner'
            ' if escalate is enabled and the message is an escalation'))

    def __str__(self):
        return '%s to %s' % (self.subscriber, self.partner)

    class Meta:
        app_label = 'uhuru'
        verbose_name = _('Delegation')
        verbose_name_plural = _('Delegations')


class EmailAddress(BaseModel, models.Model):
    subscriber = models.ForeignKey(
        Subscriber, db_index=True, blank=False, null=False)
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
        app_lable = 'uhuru'


class Telephone(BaseModel, models.Model):
    subscriber = models.ForeignKey(
        Subscriber, db_index=True, blank=False, null=False)


class Subscription(BaseModel, models.Model):
    subscription = models.CharField(
        'subscription', max_length=64, unique=True, db_index=True, blank=False,
        null=False)
    emails_list = models.TextField('subscribers', blank=False, null=False)
    from_email = models.CharField(
        'from', max_length=255, blank=True, null=True,
        default=settings.DEFAULT_FROM_EMAIL)
    template_dir = models.CharField(
        'email templates directory', max_length=255, blank=False, null=False)
    template_name = models.CharField(
        'email template name', max_length=64, blank=False, null=False)
    template_prefix = models.CharField(
        'email template prefix', max_length=64, blank=False, null=False,
        default='email/')
    headers = models.TextField(
        'data headers', blank=False, null=False,
        default='common_name,expires_in,not_before,not_after')

    def __str__(self):
        return self.subscription

    class Meta:
        app_label = 'uhuru'
