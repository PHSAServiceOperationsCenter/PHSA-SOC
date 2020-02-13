"""
.. _tasks:

:module:    mail_collector.tasks

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

Celery Tasks for the :ref:`Mail Collector Application`

"""
from smtplib import SMTPConnectError

from celery import shared_task, group
from celery.utils.log import get_task_logger

from django.db.models import Q
from django.utils import timezone

from citrus_borg.dynamic_preferences_registry import get_preference
from citrus_borg.locutus.assimilation import process_borg
from citrus_borg.models import WinlogbeatHost
from mail_collector import exceptions, models, lib, queries
from p_soc_auto_base import utils as base_utils


LOG = get_task_logger(__name__)


@shared_task(queue='mail_collector', rate_limit='5/s')
def store_mail_data(body):
    """
    Save an exchange bot event to the database

    :arg ``collections.namedtuple`` body: the event object

    :returns:

        the saved event. this will be either a
        :class:`mail_collector.models.MailBotLogEvent`
        instance if the event is a connection or an exception, or a
        :class:`mail_collector.models.MailBotMessage` instance if the
        event is a sent or a received. note that in the latter case
        a :class:`mail_collector.models.MailBotLogEvent` instance
        is created implicitly

    :raises:

        :exc:`mail_collector.exceptions.SaveExchangeEventError` if the
        :class:`mail_collector.models.MailBotLogEvent` cannot be saved

        :exc:`mail_collector.exceptions.SaveExchangeMailEventError` if the
        :class:`mail_collector.models.MailBotMessage` instance cannot be saved

    """
    try:
        exchange_borg = process_borg(body)
    except Exception as error:
        raise exceptions.BadEventDataError(
            'cannot process event data from %s, error: %s'
            % (body, str(error)))

    try:
        source_host = WinlogbeatHost.get_or_create_from_borg(
            exchange_borg)
    except Exception as error:
        raise exceptions.BadHostDataFromEventError(
            f'cannot update borg host info from {exchange_borg}, error: {error}'
            )

    event_data = exchange_borg.mail_borg_message[0]

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

    if event.event_status == 'FAIL':
        try:
            raise_failed_event_by_mail.apply_async(
                kwargs={'event_pk': event.pk})
        except Exception as error:
            # log and swallow the exception because we need to finish
            # processing this event if it comes with a mail message
            LOG.exception(error)

    if exchange_borg.mail_borg_message[1]:
        mail_data = exchange_borg.mail_borg_message[1]
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

        LOG.info('created exchange monitoring event from email message %s',
                 event.mail_message_identifier)
        return

    LOG.warning('created exchange monitoring event %s', event.uuid)


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def raise_failed_event_by_mail(event_pk):
    """
    send an alert email for failed events

    :arg int event_pk:

        the primary key of the :class:`mail_collector.models.MailBotLogEvent`
        instance with the failed event

    :returns: the result of the email operation
    :rtype: str

    :raises: :exc:`Exception` if an error is thrown by the email send op

    """
    data = models.MailBotLogEvent.objects.filter(pk=event_pk)
    subscription = base_utils.get_subscription('Exchange Client Error')

    # let's cache some data to avoid evaluating the queryset multiple times
    data_extract = data.values(
        'uuid', 'event_type',
        'source_host__site__site', 'source_host__host_name')[0]

    if base_utils.borgs_are_hailing(
            data=data, subscription=subscription,
            level=get_preference('commonalertargs__error_level'),
            event_type=data_extract.get('event_type'),
            site=data_extract.get('source_host__site__site'),
            bot=data_extract.get('source_host__host_name')):
        LOG.info('raised email alert for event %s', data_extract.get('uuid'))
        return

    LOG.warning('could not raise email alert for event %s',
                data_extract.get('uuid'))


@shared_task(queue='mail_collector')
def expire_events(moment=None):
    """
    mark events as expired. also delete them if so configured

    expired events are deleted based on the value of the
    :class:`citrus_borg.dynamic_preferences_registry.ExchangeDeleteExpired`
    dynamic settings

    :arg `datetime.datetime` moment:

        the cutoff moment; all rows older than this will be expired.
        default: ``None``. when ``None`` it will be calculated based on the
        value of the
        :class:`citrus_borg.dynamic_preferences_registry.ExchangeExpireEvents`
        dynamic setting relative to the moment returned by
        :meth:`datetime.datetime.now`

    .. todo::

        Argument type is not suitable for celery tasks. How does one
        pass a datetime from a celery beat task? This need to change to
        something that can be passed in as a string of some sorts (or a
        dictionary of basic types).

    """
    if moment is None:
        moment = base_utils.MomentOfTime.past(
            time_delta=get_preference('exchange__expire_events'))

    if not isinstance(moment, timezone.datetime):
        error = TypeError(
            'Invalid object type %s, was expecting datetime'
            % type(moment))
        LOG.error(error)
        raise error

    count_expired = models.MailBotLogEvent.objects.filter(
        event_registered_on__lte=moment).update(is_expired=True)

    if get_preference('exchange__delete_expired'):
        count_deleted_messages = models.MailBotMessage.objects.filter(
            event__is_expired=True).all().delete()

        count_deleted_events = models.MailBotLogEvent.objects.filter(
            is_expired=True).all().delete()

        LOG.info('expired %s exchange events, deleted %s exchange message'
                 ' events and %s other exchange events',
                 count_expired, count_deleted_messages,
                 count_deleted_events + count_deleted_messages)

    LOG.info('expired %s exchange log events', count_expired)


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def bring_out_your_dead(
        data_source, filter_exp, subscription, url_annotate=False,
        level=None, filter_pref=None, **base_filters):
    """
    generic task to raise email alerts about
    :ref:`Mail Collector Application` entities that have been in an
    abnormal state for a given duration measured going back from the
    current moment

    .. todo:: see `<https://trello.com/c/vav94p7e>`_

    :arg str data_source: the reference to a
        :class:`django.db.models.Model` in the form of 'app_label.model_name'

    :arg str filter_exp: a django filter lhs expression (field_name__lookup);
        it is actually geared to deal with datetime fields

    :arg str subscription: the reference to the
        :class:`ssl_cert_tracker.models.Subscription` instance to be used
        for rendering the email alert

    :arg bool url_annotate:

        extend the queryset with the entity URL; default ``False``

    :arg str level: INFO|WARN|ERROR to add to the subject line of the email
        alert; default ``None``

    :arg `object` filter_pref: either a
        :class:`django.utils.timezone.timedelta` instance or a :class:`dict`
        suitable as argument for constructing a
        :class:`django.utils.timezone.timedelta` like {'days': ``float``,
        'hours': ``float``, 'seconds': ``float``}; default ``None``.
        when ``None`` the value is picked up from the
        :class:`citrus_borg.dynamic_preferences_registry.ExchangeDefaultError`
        dynamic setting

    :arg \*\*base_filters: additional django lookup style arguments to be
        applied to the queryset

    :returns: the result of the email send operation
    :rtype: str

    :raises:

        :exc:`TypeError` if filter_pref cannot be cast to
        ``datetime.timedelta``

        :exc:`Exception` if an exception was thrown while sending the alert

    example::

        qs=dead_bodies('mail_collector.mailhost','excgh_last_seen__lte',
                    not_seen_after={'minutes': 1}, enabled=True)

    """

    if level is None:
        level = get_preference('exchange__default_level')

    subscription = base_utils.get_subscription(subscription)

    if filter_pref is None:
        filter_pref = get_preference('exchange__default_error')

    if not isinstance(filter_pref, dict):
        filter_pref = get_preference(filter_pref)
        if not isinstance(filter_pref, timezone.timedelta):
            raise TypeError(
                'Invalid object type %s. Must be datetime.timedelta.'
                % type(filter_pref)
            )

    not_seen_after = base_utils.MomentOfTime.past(time_delta=filter_pref)

    data = queries.dead_bodies(
        data_source, filter_exp, not_seen_after=not_seen_after,
        url_annotate=url_annotate, **base_filters)

    if not data and not get_preference('exchange__empty_alerts'):
        LOG.info('no %s data found for %s',
                 level, subscription.subscription)
        return

    if base_utils.borgs_are_hailing(
            data=data, subscription=subscription, time_delta=filter_pref,
            level=level):
        LOG.info('emailed data for %s', data.model._meta.verbose_name_plural)
        return

    LOG.warning('could not email data for %s',
                data.model._meta.verbose_name_plural)


# TODO unused???
@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def report_mail_between_domains(only_fails=False, subscription=None):
    """
    task to run reports about mail between domains

    :arg str subscription:

        the email subscription. default: 'Mail Verification Report'

    :arg bool only_fails: only report the fails, default: ``False``

    :returns: the result of the email send operation
    :rtype: str

    :raises: :exc:`Exception` if an exception was thrown while sending the alert

    """
    if subscription is None:
        subscription = 'Mail Verification Report'

    subscription = base_utils.get_subscription(subscription)

    queryset = models.MailBetweenDomains.objects.filter(
        enabled=True, is_expired=False)

    if only_fails:
        queryset = queryset.filter(status__iexact='FAILED')

    if base_utils.borgs_are_hailing(data=queryset, subscription=subscription):
        LOG.info('emailed report for mail between domains verification')
        return

    LOG.warning('could not email report for mail between domains verification')


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def dead_mail_sites(subscription, time_delta_pref=None, level=None):
    """
    task for site related alerts via email

    :returns:

        the return depends on whether the systems has detected alerts and
        on the value of the
        :class:`citrus_borg.dynamic_preferences_registry.ExchangeEmptyAlerts`
        dynamic setting

        *    if there are alerts, this task will return the result of the email
             send op

        *    otherwise the task will check the value of the
             :class:`citrus_borg.dynamic_preferences_registry.ExchangeEmptyAlerts`
             dynamic setting.

             *    if the value is ``False``, the task will not send any emails
                  and it will return this information

             *    otherwise the task will send an email saying that there are
                  no alerts and return the result of the email send op
    :rtype: str

    :raises: :exc:`Exception` if an exception was thrown while sending the alert

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
        LOG.info('no %s data found for %s', level, subscription.subscription)

    if base_utils.borgs_are_hailing(
            data=data, subscription=subscription, time_delta=time_delta,
            level=level):
        LOG.info('emailed data for %s', data.model._meta.verbose_name_plural)
        return

    LOG.warning('could not email data for %s',
                data.model._meta.verbose_name_plural)


@shared_task(queue='mail_collector', serializer='pickle')
def invoke_report_events_by_site(report_interval=None, report_level=None):
    """
    invoke tasks for mailing the events by site reports

    :arg `object` report_interval:

        the time interval for which the report is calculated

        it is either a :class:`datetime.timedelta` instance or a
        :class:`dict` suitable for constructing a :class:`datetime.timedelta`
        instance. it defaults to ``None`` and  when it is ``None``,
        the value is picked from
        :class:`citrus_borg.dynamic_preferences_registry.ExchangeReportInterval`

    :arg str report_level: similar to a log level, defaults to ``None``

        when ``None``, the value is picked from
        :class:`citrus_borg.dynamic_preferences_registry.ExchangeDefaultErrorLevel`


    :returns: the sites for which the report tasks have been invoked
    :rtype: str


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

    LOG.info('launched report tasks for exchange events by site for sites: %s',
             ', '.join(sites))


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def report_events_by_site(site, report_interval, report_level):
    """
    send out report with events for a site via email

    :arg str site: the site to report on

    :arg `object` report_interval: the time interval for which the report is
        calculated. it is either a :class:`datetime.timedelta` instance or a
        :class:`dict` suitable for constructing a :class:`datetime.timedelta`
        instance

    :arg str report_level: INFO|WARN|ERROR

    :returns: the result of the email send operation
    :rtype: str

    :raises:

        :exc:`Exception` if an exception was thrown while sending the alert

    """
    subscription = base_utils.get_subscription('Exchange Send Receive By Site')

    data = queries.dead_bodies(
        data_source='mail_collector.mailbotmessage',
        filter_exp='event__event_registered_on__gte',
        not_seen_after=base_utils.MomentOfTime.past(
            time_delta=report_interval),
        event__source_host__site__site=site).\
        order_by('-mail_message_identifier', 'event__event_type_sort')

    if base_utils.borgs_are_hailing(
            data=data, subscription=subscription, logger=LOG,
            time_delta=report_interval, level=report_level, site=site):
        LOG.info('emailed exchange send receive events report for site %s',
                 site)
        return

    LOG.warning('could not email exchange send receive events report for site'
                ' %s', site)


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def report_failed_events_by_site(site, report_interval):
    """
    send out report with failed events for a site via email

    :arg str site: the host (short) name of the bot to report on

    :arg `object` report_interval: the time interval for which the report is
        calculated. it is either a :class:`datetime.timedelta` instance or a
        :class:`dict` suitable for constructing a :class:`datetime.timedelta`
        instance


    :returns: the result of the email send operation
    :rtype: str

    :raises:

        :exc:`Exception` if an exception was thrown while sending the alert

    """
    subscription = base_utils.get_subscription(
        'Exchange Failed Send Receive By Site')

    data = queries.dead_bodies(
        data_source='mail_collector.mailbotmessage',
        filter_exp='event__event_registered_on__gte',
        not_seen_after=base_utils.MomentOfTime.past(
            time_delta=report_interval),
        event__source_host__site__site=site,
        event__event_status__iexact='fail').\
        order_by('-mail_message_identifier', 'event__event_type_sort')

    if base_utils.borgs_are_hailing(
            data=data, subscription=subscription, time_delta=report_interval,
            level=get_preference('exchange__server_error'), site=site):
        LOG.info('emailed exchange failed send receive events report for site'
                 ' %s', site)
        return

    LOG.warning('could not email exchange failed send receive events report for'
                ' site %s', site)


@shared_task(queue='mail_collector', serializer='pickle')
def invoke_report_events_by_bot(report_interval=None, report_level=None):
    """
    invoke tasks for mailing the events by bot reports

    :arg `object` report_interval:

        the time interval for which the report is calculated

        it is either a :class:`datetime.timedelta` instance or a
        :class:`dict` suitable for constructing a :class:`datetime.timedelta`
        instance. it defaults to ``None`` and  when it is ``None``,
        the value is picked from
        :class:`citrus_borg.dynamic_preferences_registry.ExchangeReportInterval`

    :arg str report_level: similar to a log level, defaults to ``None``

        when ``None``, the value is picked from
        :class:`citrus_borg.dynamic_preferences_registry.ExchangeDefaultErrorLevel`


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

    LOG.info('launched report tasks for exchange events by bot for bots: %s',
             ', '.join(bots))


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def report_events_by_bot(bot, report_interval, report_level):
    """
    send out report for events for a bot over a given duration measured
    back from the moment of the call  via email

    :arg str bot: the host (short) name of the bot to report on

    :arg `object` report_interval: the time interval for which the report is
        calculated. it is either a :class:`datetime.timedelta` instance or a
        :class:`dict` suitable for constructing a :class:`datetime.timedelta`
        instance

    :arg str report_level: INFO|WARN|ERROR pre-pended to the email subject line


    :returns: the result of the email send operation
    :rtype: str

    :raises:
        :exc:`Exception` if an exception was thrown while sending the alert

    """
    subscription = base_utils.get_subscription('Exchange Send Receive By Bot')

    data = queries.dead_bodies(
        data_source='mail_collector.mailbotmessage',
        filter_exp='event__event_registered_on__gte',
        not_seen_after=base_utils.MomentOfTime.past(
            time_delta=report_interval),
        event__source_host__host_name=bot).\
        order_by('-mail_message_identifier', 'event__event_type_sort')

    if base_utils.borgs_are_hailing(
            data=data, subscription=subscription, time_delta=report_interval,
            level=report_level, bot=bot):
        LOG.info('emailed exchange send receive events report for bot %s', bot)
        return

    LOG.warning('could not email exchange send receive events report for bot %s'
                , bot)


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def report_failed_events_by_bot(bot, report_interval):
    """
    send out report for failed events for a bot over a given duration measured
    back from the moment of the call  via email

    :arg str bot: the host (short) name of the bot to report on

    :arg `object` report_interval: the time interval for which the report is
        calculated. it is either a :class:`datetime.timedelta` instance or a
        :class:`dict` suitable for constructing a :classL`datetime.timedelta`
        instance, for instance {'hours': 1, 'seconds': 1}

    :returns: the result of the email send operation
    :rtype: str

    :raises:

        :exc:`Exception` if an exception was thrown while sending the alert

    """
    subscription = base_utils.get_subscription(
        'Exchange Failed Send Receive By Bot')

    data = queries.dead_bodies(
        data_source='mail_collector.mailbotmessage',
        filter_exp='event__event_registered_on__gte',
        not_seen_after=base_utils.MomentOfTime.past(
            time_delta=report_interval),
        event__source_host__host_name=bot,
        event__event_status__iexact='fail').\
        order_by('-mail_message_identifier', 'event__event_type_sort')

    if base_utils.borgs_are_hailing(
            data=data, subscription=subscription, time_delta=report_interval,
            level=get_preference('exchange__server_error'), bot=bot):
        LOG.info('emailed exchange failed send receive events report for bot %s'
                 , bot)

    LOG.warning('could not email exchange failed send receive events report'
                ' for bot %s', bot)


@shared_task(queue='mail_collector', rate_limit='3/s', max_retries=3,
             serializer='pickle', retry_backoff=True,
             autoretry_for=(SMTPConnectError,))
def raise_site_not_configured_for_bot():
    """
    email alerts if there are exchange bots with mis-configured site info
    """
    data = models.MailHost.objects.filter(
        Q(site__isnull=True) | Q(site__site__iexact='site.not.exist')).\
        exclude(host_name__iexact='host.not.exist')

    if data.exists():
        data = base_utils.url_annotate(data)

    if not data and not get_preference('exchange__empty_alerts'):
        LOG.info('all exchange bots are properly configured')

    if base_utils.borgs_are_hailing(
            data=data,
            subscription=base_utils.get_subscription('Exchange bot no site'),
            level=get_preference('exchange__server_error')):
        LOG.info('emailed alert for mis-configured Exchange bots')

    LOG.warning('cannot email alert for mis-configured Exchange bots')
