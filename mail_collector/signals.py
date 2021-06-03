"""
.. _signals:

:module:    mail_collector.signals

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

Django Signals Module for the :ref:`Mail Collector Application`

"""
from logging import getLogger

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    MailBotLogEvent, MailBotMessage, ExchangeServer, ExchangeDatabase,
    MailBetweenDomains, MailSite,
)

LOG = getLogger(__name__)


# pylint: disable=unused-argument


@receiver(post_save, sender=MailBotMessage)
def update_mail_between_domains(sender, instance, *args, **kwargs):
    """
    **Create** or **update** entries in
    :class:`mail_collector.models.MailBetweenDomains` after applicable
    exchange bot events have been created or updated in
    :class:`mail_collector.models.MailBotMessage`

    An entry in the domain to domain verification model requires a send and
    a receive event for the same message identifier.
    Since one cannot have a receive event unless a matching send event
    has already been generated, this function looks for all receive events.

    An :class:`mail_collector.models.MailBotMessage` instance that contains a
    receive event with a status of PASS is considered to be the sign of
    a successful email transmission between the email MX domain of the
    sender and the email MX domain of the receiver and a note of this is made
    in the :class:`mail_collector.models.MailBetweenDomains` model

    The site entry in the domain to domain verification is extracted from the
    :attr:`mail_collector.models.MailBotMessage.event.event_group_id` value.
    this attribute is in the format $site+$host_name+$timestamp

    :Note:

        This functionality is absolutely dependent on the convention
        described above. This convention is under our control since
        it is implemented via the `Mail Borg Client Application <https://github.com/PHSAServiceOperationsCenter/MailBorg>`_.
        Please do not mess with success.

    The from domain is extracted from the
    :attr:`mail_collector.models.MailBotMessage.sent_from` field in the
    instance.

    The to domain is extracted from the
    :attr:`mail_collector.models.MailBotMessage.received_by` field of the
    received event.

    :returns: a :class:`str` with the data that was updated or ``None``

    """
    LOG.info('Updating mail_between_domains')
    if instance.event.event_type != 'receive':
        # only received event have all the info that we need. skip others
        LOG.info("Received a %s event, no further action taken.",
                 instance.event.event_type)
        return

    if not sender.objects.filter(
            mail_message_identifier__exact=instance.mail_message_identifier).\
            filter(event__event_type__exact='send').exists():
        LOG.info("Message %s does not match a sent message in our database.",
                 instance)
        return

    try:
        site = MailSite.objects.get(
            site=instance.event.event_group_id.split('+')[0])
    except MailSite.DoesNotExist:
        site = MailSite(site=site)
        site.save()

    from_domain = instance.sent_from.split('@')[1]

    if not instance.sent_to:
        # the receive event is incomplete thus it failed, bail
        LOG.info("Message %s does not have a received by.", instance)
        return

    # There should only be a single email in a received message
    to_domain = instance.sent_to[0].split('@')[1]

    last_updated_from_node_id = instance.event.source_host.orion_id

    verified_mail = MailBetweenDomains.objects.filter(
        site=site,
        from_domain__iexact=from_domain, to_domain__iexact=to_domain)
    if verified_mail.exists():
        verified_mail = verified_mail.get()
    else:
        verified_mail = MailBetweenDomains(site=site,
                                           from_domain=from_domain,
                                           to_domain=to_domain)

    verified_mail.status = 'PASS'
    if 'FAIL' in sender.objects.filter(
            mail_message_identifier__iexact=instance.mail_message_identifier).\
            values_list('event__event_status', flat=True):
        verified_mail.status = 'FAIL'

    verified_mail.last_verified = timezone.now()
    verified_mail.last_updated_from_node_id = last_updated_from_node_id
    verified_mail.save()

    LOG.info('Verified mail updated %s: %s->%s, %s',
             verified_mail.site, verified_mail.from_domain,
             verified_mail.to_domain, verified_mail.status)


@receiver(post_save, sender=MailBotLogEvent)
def update_exchange_entities_from_event(sender, instance, *args, **kwargs):
    """
    **Create** or **update** :class:`mail_collector.models.ExchangeServer`
    instances from Exchange connection events

    The conventions described in :func:`update_exchange_entities_from_message`
    apply here as well.

    :returns: the updated :class:`mail_collector.models.ExchangeServer`
        instance
    """
    if instance.event_status != 'PASS' or instance.event_type != 'connection' \
            or '-' not in instance.mail_account:
        # only interested in successful connections for server specific accounts
        # these accounts are formatted z-[server]-[database]
        # other accounts are used to send messages, but supply no info about
        # specific servers
        return None

    LOG.info('Updating exchange entities')
    exchange_server_name = instance.mail_account.split('-')[1]

    try:
        exchange_server = ExchangeServer.objects.get(
            exchange_server=exchange_server_name)
    except ExchangeServer.DoesNotExist:
        exchange_server = ExchangeServer(exchange_server=exchange_server)

    exchange_server.last_connection = instance.event_registered_on
    exchange_server.save()

    LOG.info('Updated last connection for %s to %s',
             exchange_server_name, str(instance.event_registered_on))

    return exchange_server


@receiver(post_save, sender=MailBotMessage)
def update_exchange_entities_from_message(sender, instance, *args, **kwargs):
    """
    **Create** or **update** Exchange backend entities from send or receive
    email events

    Exchange backend entities:

    *    :class:`mail_collector.models.ExchangeServer`

    *    :class:`mail_collector.models.ExchangeDatabase`

    The datetime fields in both models are used to keep track of when the
    most recent Exchange event has been recorded. The models also keep track
    of where said event is originated from.

    Events are being correlated with Exchange entities based on the
    Exchange account. By convention the Exchange account contains
    the name of the Exchange server and the name of the Exchange database
    instance as follows: z-$ServerName-$DatabaseName@mx_domain.ca.

    :returns: a :class:`tuple` with the updated Exchange entity instance
        and the event type that caused the update
    """
    if instance.event.event_status != 'PASS' \
            or instance.event.event_type not in ['send', 'receive']:
        LOG.info("Not updating exchange entities for event with status %s and type %s",
                 instance.event.event_status, instance.event.event_type)
        return None

    updated_resources = []

    LOG.debug('sent to is %s', instance.sent_to)

    for account_str in instance.sent_to:
        LOG.debug('account string is %s', account_str)
        exchange_server, database = account_str.split('-')[1:3]
        database = database.split('@')[0]
        last_updated_from_node_id = instance.event.source_host.orion_id

        LOG.info('Updating exchange entities. Server %s database %s',
                 exchange_server, database)

        try:
            exchange_server = ExchangeServer.objects.get(
                exchange_server=exchange_server)
        except ExchangeServer.DoesNotExist:
            exchange_server = ExchangeServer(exchange_server=exchange_server)
            exchange_server.save()

        exchange_server.last_updated_from_node_id = last_updated_from_node_id

        if instance.event.event_type == 'send':
            exchange_server.last_send = instance.event.event_registered_on
            exchange_server.save()

            LOG.info("Event was a send, not updating database")

            updated_resources.append(exchange_server)

            continue

        exchange_server.last_inbox_access = instance.event.event_registered_on
        exchange_server.save()

        try:
            database = ExchangeDatabase.objects.get(
                database=database)
            database.last_access = instance.event.event_registered_on
        except ExchangeDatabase.DoesNotExist:
            database = ExchangeDatabase(
                database=database, exchange_server=exchange_server,
                last_access=instance.event.event_registered_on)

        database.last_updated_from_node_id = last_updated_from_node_id
        database.save()

        updated_resources.append(database)

    return updated_resources, instance.event.event_type

# pylint: enable=unused-argument
