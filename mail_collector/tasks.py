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

from celery import shared_task, group
from celery.utils.log import get_task_logger

from django.utils import timezone


from citrus_borg.locutus.assimilation import process_borg
from citrus_borg.models import WinlogbeatHost
from citrus_borg.dynamic_preferences_registry import get_preference

from mail_collector import exceptions, models, lib, queries
from p_soc_auto_base import utils as base_utils

LOGGER = get_task_logger(__name__)


@shared_task(queue='mail_collector', rate_limit='5/s')
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

        # is this a failed event? if so, raise the alarm
        # TODO: also need to call something that updates the orion_flash
        if event.event_status in ['FAIL']:
            try:
                raise_failed_event_by_mail(event_pk=event.pk)
            except:  # pylint: disable=bare-except
                # swallow the exception because we need to finish
                # processing this event if it comes with a mail message
                pass

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


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def raise_failed_event_by_mail(event_pk):
    """
    send an alert email for failed events

    # TODO: template and subscription
    """
    data = models.MailBotLogEvent.objects.filter(pk=event_pk)
    subscription = base_utils.get_subscription('Exchange Client Error')

    # let's cache some data to avoid evaluating the queryset multiple times
    data_extract = data.values(
        'uuid', 'event_type',
        'source_0host__site__site', 'source_host__host_name')[0]

    try:
        ret = base_utils.borgs_are_hailing(
            data=data, subscription=subscription, logger=LOGGER,
            level=get_preference('exchange__server_error'),
            event_type=data_extract.get('event_type'),
            site=data_extract.get('source_host__site__site'),
            bot=data_extract('source_host__host_name'))
    except Exception as error:
        raise error

    if ret:
        return 'raised email alert for event %s' % str(
            data_extract.get('uuid'))

    return 'could not raise email alert for event %s' % str(
        data_extract.get('uuid'))


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
def bring_out_your_dead(  # pylint: disable=too-many-arguments
        data_source, filter_exp, subscription, url_annotate=False,
        level=None, filter_pref=None, **base_filters):
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

    some tasks to implement:

    qs=dead_bodies('mail_collector.mailhost','excgh_last_seen__lte',
                    not_seen_after={'minutes': 1}, enabled=True)

    the below is not correct; see the trick documented in queries
    qs=dead_bodies('mail_collector.mailsite','winlogbeathost__excgh_last_seen__lte',
                    not_seen_after={'minutes': 1}, enabled=True)

    must raise the failed email verifications here; there is a bug that
    doesn't allow doing it from signals
    """

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

    try:
        ret = base_utils.borgs_are_hailing(
            data=data, subscription=subscription, logger=LOGGER,
            time_delta=filter_pref, level=level)
    except Exception as error:
        raise error

    if ret:
        return 'emailed data for %s' % data.model._meta.verbose_name_plural

    return 'could not email data for %s' % data.model._meta.verbose_name_plural


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def dead_mail_sites(subscription: str, time_delta_pref: str = None,
                    level: str = None) -> str:
    """
    task for diseminating site related info via email
    """
    if level is None:
        level = get_preference('exchange__default_level')

    subscription = base_utils.get_subscription(subscription)

    if time_delta_pref is None:
        time_delta = get_preference('exchange__default_error')
    else:
        time_delta = get_preference(time_delta_pref)

    not_seen_after = base_utils.MomentOfTime.past(time_delta=time_delta)

    data = queries.dead_mail_sites(not_seen_after=not_seen_after)

    if not data and not get_preference('exchange__empty_alerts'):
        return 'no %s data found for %s' % (level, subscription.subscription)

    try:
        ret = base_utils.borgs_are_hailing(
            data=data, subscription=subscription, logger=LOGGER,
            time_delta=time_delta, level=level)
    except Exception as error:
        raise error

    if ret:
        return 'emailed data for %s' % data.model._meta.verbose_name_plural

    return 'could not email data for %s' % data.model._meta.verbose_name_plural


@shared_task(queue='mail_collector', serializer='pickle')
def invoke_report_events_by_site(report_interval=None, report_level=None):
    """
    invoke the tasks for emailing events by site reports

    """
    if report_interval is None:
        report_interval = get_preference('exchange__report_interval')

    if report_level is None:
        report_level = get_preference('exchange__report_level')

    sites = list(
        base_utils.get_base_queryset('mail_collector.mailsite', enabled=True).
        values_list('site', flat=True)
    )

    group(report_events_by_site.s(site, report_interval, report_level)
          for site in sites)()

    group(report_failed_events_by_site.s(site, report_interval)
          for site in sites)()

    return ('launched report tasks for exchange events by site'
            ' for sites: %s' % ', '.join(sites))


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def report_events_by_site(site, report_interval, report_level):
    """
    send out report with events for a site via email
    """
    subscription = base_utils.get_subscription('Exchange Send Receive By Site')

    data = queries.dead_bodies(
        data_source='mail_collector.mailbotmessage',
        filter_exp='event__event_registered_on__gte',
        not_seen_after=report_interval,
        event__event_source_host__site__site=site).\
        order_by('-mail_message_identifier', 'event__event_type_sort')

    try:
        ret = base_utils.borgs_are_hailing(
            data=data, subscription=subscription, logger=LOGGER,
            time_delta=report_interval, level=report_level, site=site)
    except Exception as error:
        raise error

    if ret:
        return (
            'emailed exchange send receive events report for site %s' % site)

    return (
        'could not email exchange send receive events report for site %s'
        % site)


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def report_failed_events_by_site(site, report_interval):
    """
    send out report with events for a site via email
    """
    subscription = base_utils.get_subscription(
        'Exchange Failed Send Receive By Site')

    data = queries.dead_bodies(
        data_source='mail_collector.mailbotmessage',
        filter_exp='event__event_registered_on__gte',
        not_seen_after=report_interval,
        event__event_source_host__site__site=site,
        event__event_status__iexact='fail').\
        order_by('-mail_message_identifier', 'event__event_type_sort')

    try:
        ret = base_utils.borgs_are_hailing(
            data=data, subscription=subscription, logger=LOGGER,
            time_delta=report_interval,
            level=get_preference('exchange__server_error'), site=site)
    except Exception as error:
        raise error

    if ret:
        return (
            'emailed exchange failed send receive events report for site %s'
            % site)

    return (
        'could not email exchange failed send receive events report for site %s'
        % site)


@shared_task(queue='mail_collector', serializer='pickle')
def invoke_report_events_by_bot(report_interval=None, report_level=None):
    """
    invoke tasks for mailing the events by bot reports

    :arg report_interval: the reporting period going back from now()
    :type report_interval: ``datetime.timedelta``

    :arg str report_level: similar to a log level

    :returns: the bots for which the report tasks have been invoked
    :rtype: str

    """
    if report_interval is None:
        report_interval = get_preference('exchange__report_interval')

    if report_level is None:
        report_level = get_preference('exchange__report_level')

    bots = list(
        base_utils.get_base_queryset('mail_collector.mailhost', enabled=True).
        values_list('host_name', flat=True)
    )

    group(report_events_by_bot.s(bot, report_interval, report_level)
          for bot in bots)()

    group(report_failed_events_by_bot.s(bot, report_interval)
          for bot in bots)()

    return ('launched report tasks for exchange events by bot'
            ' for bots: %s' % ', '.join(bots))


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def report_events_by_bot(bot, report_interval, report_level):
    """
    send out report for events for a bot via email

    """
    subscription = base_utils.get_subscription('Exchange Send Receive By Bot')

    data = queries.dead_bodies(
        data_source='mail_collector.mailbotmessage',
        filter_exp='event__event_registered_on__gte',
        not_seen_after=report_interval,
        event__event_source_host__host_name=bot).\
        order_by('-mail_message_identifier', 'event__event_type_sort')

    try:
        ret = base_utils.borgs_are_hailing(
            data=data, subscription=subscription, logger=LOGGER,
            time_delta=report_interval, level=report_level, bot=bot)
    except Exception as error:
        raise error

    if ret:
        return (
            'emailed exchange send receive events report for bot %s' % bot)

    return (
        'could not email exchange send receive events report for bot %s'
        % bot)


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def report_failed_events_by_bot(bot, report_interval):
    """
    send out report for failed events for a bot via email

    """
    subscription = base_utils.get_subscription(
        'Exchange Failed Send Receive By Bot')

    data = queries.dead_bodies(
        data_source='mail_collector.mailbotmessage',
        filter_exp='event__event_registered_on__gte',
        not_seen_after=report_interval,
        event__event_source_host__host_name=bot,
        event__event_status__iexact='fail').\
        order_by('-mail_message_identifier', 'event__event_type_sort')

    try:
        ret = base_utils.borgs_are_hailing(
            data=data, subscription=subscription, logger=LOGGER,
            time_delta=report_interval,
            level=get_preference('exchange__server_error'), bot=bot)
    except Exception as error:
        raise error

    if ret:
        return (
            'emailed exchange failed send receive events report for bot %s'
            % bot)

    return (
        'could not email exchange failed send receive events report for bot %s'
        % bot)
