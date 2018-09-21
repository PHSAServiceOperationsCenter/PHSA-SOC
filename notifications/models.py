"""
#TODO: write a validator that makes sure that in models with is_default,
there can be one and only one record with is_default set to True
"""
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone

from p_soc_auto_base.models import BaseModel


class NotificationType(BaseModel, models.Model):
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
    delete_if_expired = models.BooleanField(
        _('delete if expired'), db_index=True, blank=False, null=False,
        default=False)
    notification_broadcast = models.ManyToManyField(
        'Broadcast', through='NotificationTypeBroadcast',
        verbose_name=_('Send Notifications of this Type Via'))
    is_default = models.BooleanField(
        _('is the default'), db_index=True, blank=False, null=False,
        default=True, help_text=_('use this notification type as the default'))
    subscribers = models.CharField(
        _('subscribers'), max_length=253, blank=True, null=True,
        help_text=_('use as placeholder for a subscription application'))
    escalation_subscribers = models.CharField(
        _('escalation subscribers'), max_length=253, blank=True, null=True,
        help_text=_('use as placeholder for a subscription application'))


class Broadcast(BaseModel, models.Model):
    broadcast = models.CharField(
        _('broadcast method'), db_index=True, unique=True, blank=False,
        null=False, max_length=64)
    is_default = models.BooleanField(
        _('is the default'), db_index=True, blank=False, null=False,
        default=True, help_text=_('use this broadcast method as the default'))


class NotificationTypeBroadcast(BaseModel, models.Model):
    notification_type = models.ForeignKey(
        'NotificationType', on_delete=models.CASCADE,
        db_index=True, blank=False, null=False,
        verbose_name=_('Send notifications of this type'))
    broadcast = models.ForeignKey(
        'Broadcast', on_delete=models.CASCADE,
        db_index=True, blank=False, null=False,
        verbose_name=_('via'))


class NotificationLevel(BaseModel, models.Model):
    notification_level = models.CharField(
        _('broadcast method'), db_index=True, unique=True, blank=False,
        null=False, max_length=16)
    is_default = models.BooleanField(
        _('is the default'), db_index=True, blank=False, null=False,
        default=True,
        help_text=_('use this notification level as the default'))


class Notification(BaseModel, models.Model):
    rule_applies = models.ForeignKey(
        'rules_engine.RuleApplies', on_delete=models.PROTECT, db_index=True,
        blank=False, null=False, verbose_name=_('raised by'))
    msg = models.CharField(
        'notification', max_length=253, db_index=True, unique=True,
        blank=False, null=False)
    notification_type = models.ForeignKey(
        'NotificationType', on_delete=models.PROTECT, db_index=True,
        blank=False, null=False, verbose_name=_('Notification Type'))
    notification_level = models.ForeignKey(
        'NotificationLevel', on_delete=models.PROTECT, db_index=True,
        blank=False, null=False, verbose_name=_('Notification Level'))
    ack_on = models.DateTimeField(
        _('acknowledged at'), db_index=True, blank=True, null=True)
    esc_ack_on = models.DateTimeField(
        _('escalation acknowledged at'), db_index=True, blank=True, null=True)
    expired_on = models.DateTimeField(
        _('expired at'), db_index=True, blank=True, null=True),
    notification_id = models.UUIDField(db_index=True, blank=True, null=True)
    instance_pk = models.BigIntegerField(pk = True)

    def _get_msg(self):
        "Returns the msg."
        return '%s' % (self.msg)
    message = property(_get_msg)


class NotificationResponse(BaseModel, models.Model):
    notification = models.ForeignKey(
        'Notification', db_index=True, blank=False, null=False,
        on_delete=models.CASCADE)
