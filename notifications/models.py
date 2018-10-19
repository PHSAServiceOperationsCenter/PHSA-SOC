"""
.. _models:

django models for the notifications app

:module:    p_soc_auto.notifications.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca
:contact:    ali.rahmat@phsa.ca

:update:    sep. 24, 2018

"""
import json

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from jsonfield import JSONField

from p_soc_auto_base.models import BaseModel
from p_soc_auto_base.utils import remove_duplicates


def _validate_is_default(obj):
    """
    in some models there can be one and only one row marked as default
    """
    if obj.is_default \
            and obj._meta.model.objects.filter(is_default=True).count() >= 1:
        default_obj = obj._meta.model.objects.filter(is_default=True).first()
        raise ValidationError(
            {'is_default':
             _('there already is a default entry in %s: %s' %
               (obj._meta.verbose_name_plural, default_obj))
             }
        )


class NotificationType(BaseModel, models.Model):
    """
    notification types model
    """
    notification_type = models.CharField(
        _('Notification Type'), db_index=True, unique=True, blank=False,
        null=False, max_length=128)
    ack_within = models.DurationField(
        _('requires acknowledgement within'), db_index=True, blank=True,
        null=True, default=timezone.timedelta(hours=2))
    escalate_within = models.DurationField(
        _('escalate if not acknowledged within'), db_index=True, blank=True,
        null=True, default=timezone.timedelta(hours=4))
    expire_within = models.DurationField(
        _('expires after'), db_index=True, blank=True,
        null=True, default=timezone.timedelta(hours=144))
    expires_automatically = models.BooleanField(
        _('expires automatically'), db_index=True, blank=False, null=False,
        default=False)
    delete_if_expired = models.BooleanField(
        _('delete if expired'), db_index=True, blank=False, null=False,
        default=False)
    notification_broadcast = models.ManyToManyField(
        'Broadcast', through='NotificationTypeBroadcast',
        verbose_name=_('Send Notifications of this Type Via'))
    is_default = models.BooleanField(
        _('is the default'), db_index=True, blank=False, null=False,
        default=False,
        help_text=_('use this notification type as the default'))
    subscribers = models.TextField(
        _('rule subscribers'), blank=True, null=True,
        help_text=_('send notifications of this type to these users.'
                    ' this will be replaced by a reference once a'
                    ' subscriptions application becomes available'))
    escalation_subscribers = models.TextField(
        _('rule escalation subscribers'), blank=True, null=True,
        help_text=_('send escalation notifications of this type to'
                    ' these users.'
                    ' this will be replaced by a reference once a'
                    ' subscriptions application becomes available'))

    def __str__(self):
        return self.notification_type

    def clean(self):
        """
        override to provide custom validation
        """
        _validate_is_default(obj=self)

    def save(self, *args, **kwargs):
        """
        override the save() method to make sure model validation is performed
        """
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Notification Type')
        verbose_name_plural = _('Notification Types')


class Broadcast(BaseModel, models.Model):
    """
    broadcast methods model
    """
    broadcast = models.CharField(
        _('broadcast method'), db_index=True, unique=True, blank=False,
        null=False, max_length=64)
    is_default = models.BooleanField(
        _('is the default'), db_index=True, blank=False, null=False,
        default=False, help_text=_('use this broadcast method as the default'))

    def __str__(self):
        return self.broadcast

    def clean(self):
        """
        override to provide custom validation
        """
        _validate_is_default(obj=self)

    def save(self, *args, **kwargs):
        """
        override the save() method to make sure model validation is performed
        """
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Broadcast Method')
        verbose_name_plural = _('Broadcast Methods')


class NotificationTypeBroadcast(BaseModel, models.Model):
    """
    custom manytomany model between notification types and broadcasts
    """
    notification_type = models.ForeignKey(
        'NotificationType', on_delete=models.CASCADE,
        db_index=True, blank=False, null=False,
        verbose_name=_('Send notifications of this type'))
    broadcast = models.ForeignKey(
        'Broadcast', on_delete=models.CASCADE,
        db_index=True, blank=False, null=False,
        verbose_name=_('via'))

    def __str__(self):
        return 'send %s via %s' % (self.notification_type, self.broadcast)

    class Meta:
        unique_together = (('notification_type', 'broadcast',),)
        verbose_name = _('Notification Type Broadcast Method')
        verbose_name_plural = _('Notification Type Broadcast Methods')


class NotificationLevel(BaseModel, models.Model):
    """
    notification level model
    """
    notification_level = models.CharField(
        _('notification level'), db_index=True, unique=True, blank=False,
        null=False, max_length=16)
    is_default = models.BooleanField(
        _('is the default'), db_index=True, blank=False, null=False,
        default=False,
        help_text=_('use this notification level as the default'))

    def __str__(self):
        return self.notification_level

    def clean(self):
        """
        override to provide custom validation
        """
        _validate_is_default(obj=self)

    def save(self, *args, **kwargs):
        """
        override the save() method to make sure model validation is performed
        """
        self.full_clean()
        super().save(*args, **kwargs)

    class Meta:
        verbose_name = _('Notification Level')
        verbose_name_plural = _('Notification Levels')


class Notification(BaseModel, models.Model):
    """
    notifications model
    """
    rule_applies = models.ForeignKey(
        'rules_engine.RuleApplies', on_delete=models.PROTECT, db_index=True,
        blank=False, null=False, verbose_name=_('raised by'))
    rule_msg = models.TextField(
        _('rule message'), blank=False, null=False)
    ack_on = models.DateTimeField(
        _('acknowledged at'), db_index=True, blank=True, null=True)
    esc_on = models.DateTimeField(
        _('escalated at'), db_index=True, blank=True, null=True)
    esc_ack_on = models.DateTimeField(
        _('escalation acknowledged at'), db_index=True, blank=True, null=True)
    expired_on = models.DateTimeField(
        _('expired at'), db_index=True, blank=True, null=True)
    broadcast_on = models.DateTimeField(
        _('broadcast at'), db_index=True, blank=True, null=True)
    notification_uuid = models.UUIDField(
        _('UUID'), db_index=True, unique=True, blank=False, null=False)
    instance_pk = models.BigIntegerField(
        _('notification object row identifier'), db_index=True, blank=True,
        null=True)
    notification_type = models.ForeignKey(
        NotificationType, db_index=True, blank=False, null=False,
        on_delete=models.PROTECT, verbose_name=_('Notification Type'))
    notification_level = models.ForeignKey(
        NotificationLevel, on_delete=models.PROTECT,
        db_index=True,
        blank=False, null=False, verbose_name=_('Notification Level'))

    @property
    def message(self):
        """
        notification message

        at this point let's make it a dictionary, it's the easiest data
        structure to shuttle around as either json or a django template
        context
        """
        ret = dict(notification_uuid=self.notification_uuid,
                   created_on=self.created_on,
                   rule=self.rule_applies.rule.rule,
                   rule_msg=json.loads(self.rule_msg),
                   object_type=self.rule_applies.content_type.model,
                   object_field=self.rule_applies.field_name,
                   etc='other things to add here...',
                   second_object_field=self.rule_applies.second_field_name,
                   )

        return ret

    @property
    def subscribers(self):
        """
        send this notification to these people
        """
        return remove_duplicates(
            '{},{},{}'.format(self.rule_applies.subscribers,
                              self.rule_applies.rule.subscribers,
                              self.notification_type.subscribers)
        )

    @property
    def escalation_subscribers(self):
        """
        escalate this notification to these people
        """
        return remove_duplicates(
            '{},{},{}'.format(
                self.rule_applies.escalation_subscribers,
                self.rule_applies.rule.escalation_subscribers,
                self.notification_type.escalation_subscribers)
        )

    def __str__(self):
        return '%s raised on %s' % (self.notification_uuid, self.created_on)


class NotificationResponse(BaseModel, models.Model):
    notification = models.ForeignKey(
        'Notification', db_index=True, blank=False, null=False,
        on_delete=models.CASCADE)
    is_ack_message = models.BooleanField(
        _('this is the acknowledgement message'), db_index=True, blank=False,
        null=False, default=False)

    def __str__(self):
        return self.notes

    class Meta:
        verbose_name = _('Notification Response')
        verbose_name_plural = _('Notification Responses')
