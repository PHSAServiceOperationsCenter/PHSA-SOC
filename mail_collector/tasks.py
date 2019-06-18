"""
.. _tasks:

celery tasks for the mail_collector application

:module:    mail_collector.tasks

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    May 27, 2019

"""
from smtplib import SMTPConnectError

from celery import shared_task, chain
from celery.utils.log import get_task_logger

from django.utils import timezone


from citrus_borg.locutus.assimilation import process_borg
from citrus_borg.models import WinlogbeatHost
from citrus_borg.dynamic_preferences_registry import get_preference

from mail_collector import exceptions, models, lib, queries
from p_soc_auto_base import utils as base_utils

LOGGER = get_task_logger(__name__)


@shared_task(queue='mail_collector')
def store_mail_data(body):
    """
    grab the exchange events from rabbitmq and dump it to the database
    """
    try:
        exchange_borg = process_borg(body, LOGGER)
    except Exception as error:
        raise exceptions.BadEventDataError(
            'cannot process event data from %s, error: %s'
            % (body, str(error)))

    try:
        source_host = WinlogbeatHost.get_or_create_from_borg(
            exchange_borg)
    except Exception as error:
        raise exceptions.BadHostDataFromEventError(
            'cannot update borg host info from %s, error: %s'
            % str(exchange_borg, str(error)))

    event_data = exchange_borg.mail_borg_message[0]

    try:
        event = models.MailBotLogEvent(
            source_host=source_host,
            event_group_id=event_data.event_group_id,
            event_status=event_data.event_status,
            event_type=event_data.event_type,
            event_type_sort=lib.event_sort_code(event_data.event_type),
            mail_account=event_data.mail_account,
            event_message=event_data.event_message,
            event_body=event_data.event_body,
            event_exception=event_data.event_exception)
        event.save()
    except Exception as error:
        raise exceptions.SaveExchangeEventError(
            'cannot save event %s, error: %s' % (str(event_data), str(error)))

    if exchange_borg.mail_borg_message[1]:
        mail_data = exchange_borg.mail_borg_message[1]
        try:
            event = models.MailBotMessage(
                event=event,
                mail_message_identifier=mail_data.mail_message_identifier,
                sent_from=mail_data.sent_from, sent_to=mail_data.sent_to,
                received_from=mail_data.received_from,
                received_by=mail_data.received_by,
                mail_message_created=mail_data.mail_message_created,
                mail_message_sent=mail_data.mail_message_sent,
                mail_message_received=mail_data.mail_message_received)
            event.save()
        except Exception as error:
            raise exceptions.SaveExchangeMailEventError(
                'cannot save event %s, error: %s' % (str(event_data),
                                                     str(error)))

        return ('created exchange monitoring event from email message %s'
                % event.mail_message_identifier)

    return 'created exchange monitoring event %s' % event.uuid


@shared_task(queue='mail_collector')
def expire_events(data_source, moment=None):
    """
    expire and/or delete events

    expired events are deleted based on
    :class:`<citru_borg.dynamic_preferences_registry.ExchangeDeleteExpired>`

    :arg str data_source:

        'app_label.model_name' info for the model that needs purging

    :arg ``datetime.datetime``:

        the cutoff moment of time; all row older than this will be expired.
        default: ``None``
        when ``Nne`` it will be calculated based on
        :class:`<citru_borg.dynamic_preferences_registry.ExchangeExpireEvents>`
        relative to :method:`<datetime.datetime.now>`
    """
    if moment is None:
        moment = base_utils.MomentOfTime.past(
            time_delta=get_preference('exchange__expire_events'))

    if not isinstance(moment, timezone.datetime):
        error = TypeError(
            'Invalid object type %s, was expecting datetime'
            % type(moment))
        LOGGER.error(error)
        raise error

    try:
        queryset = base_utils.get_base_queryset(
            data_source, event_registered_on__lte=moment)
    except Exception as error:
        LOGGER.error(error)
        raise error

    count, operation = queryset.update(is_expired=True), 'expired'

    if get_preference('exchange__delete_expired'):
        count, operation = queryset.all().delete(), 'deleted'

    return '{} {} older than {:%c} have been {}'.format(
        count, queryset.model._meta.verbose_name_plural, moment, operation)


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def bring_out_your_dead(
        data_source, filter_exp, subscription, url_annotate=False,
        level=None, filter_pref=None, by_mail=True, to_orion=False,
        **base_filters):
    """
    example::

        queries.dead_bodies(exc_servers, last_connected, not_seen_for_warn,
        enabled=True)

        do it for all the fields in exc_servers and ofr each of those for
        both warn and critical

        same thing for exc_databases

        same thing for exchange clients. see if it can be done for exchange
        sites


    extra_context: filter_pref, level
    """
    task_returns = 'data dispatched:'

    if level is None:
        level = get_preference('exchange__default_level')

    subscription = base_utils.get_subscription(subscription)

    if filter_pref is None:
        filter_pref = get_preference('exchange__default_error')
    else:
        filter_pref = get_preference(filter_pref)

    not_seen_after = base_utils.MomentOfTime.past(time_delta=filter_pref)

    data = queries.dead_bodies(
        data_source, filter_exp, not_seen_after=not_seen_after,
        url_annotate=url_annotate, **base_filters)

    if not data and not get_preference('exchange__empty_alerts'):
        return 'no %s data found for %s' % (level, subscription.subscription)

    if by_mail:
        send_mail.s(data=data, subscription=subscription, logger=LOGGER,
                    time_delta=filter_pref, level=level).apply_async()
        task_returns = '{} {}'.format(task_returns, 'by mail')

    if to_orion:
        raise NotImplementedError
        # task_returns = '{}, {}'.format(task_returns, 'to orion')

    return task_returns


@shared_task(queue='email', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def send_mail(data=None, subscription=None, logger=LOGGER, **extra_context):
    """
    task wrapper for calling
    :method:`<p_soc_auto_base.utils.borgs_are_hailing>`
    """
    if data is None:
        raise ValueError('cannot send email without data')

    if subscription is None:
        raise ValueError('cannot send email without subscription info')

    try:
        return base_utils.borgs_are_hailing(
            data=data, subscription=subscription, logger=logger,
            **extra_context)
    except Exception as error:
        raise error
