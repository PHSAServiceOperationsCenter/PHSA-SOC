"""
.. _signals:

django models for the mail_collector app

:module:    mail_collector.signals

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    jun. 10, 2019

"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import (
    MailBotLogEvent, MailBotMessage, ExchangeServer, ExchangeDatabase,
    MailBetweenDomains, MailSite,
)

# pylint: disable=unused-argument


@receiver(post_save, sender=MailBotMessage)
def update_mail_between_domains(sender, instance, *args, **kwargs):
    """
    create or update entries in
    :class:`<mail_collector.models.MailBetweenDomains>`

    an entry in the domain to domain verification requires a send and a receive
    event for the same message identifier.

    the domain to domain verification status depends on the event_status of
    the send and receive events. if either event_status is FAIL,
    the verification status is FAIL as well.

    the site entry in the domain to domain verification is extracted from the
    event_group_id value.
    the from domain is extracted from the sent_from field in the instance.
    the to domain is extracted from the received_by field of the received event

    """
    if not sender.objects.filter(
            mail_message_identifier__exact=instance.mail_message_identifier).\
            count() == 2:
        # we don't have a quorum, go away
        return None

    if instance.event.event_type not in ['receive']:
        # only received event have all the info that we need. skip others
        return None

    try:
        site = MailSite.objects.get(
            site=instance.event.event_group_id.split('+')[0])
    except MailSite.DoesNotExist:
        site = MailSite(site=site)
        site.save()

    from_domain = instance.sent_from.split('@')[1]
    to_domain = instance.received_by.split('@')[1]
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

    return '{}: {}->{}, {}'.format(
        verified_mail.site, verified_mail.from_domain,
        verified_mail.to_domain, verified_mail.status)


@receiver(post_save, sender=MailBotLogEvent)
def update_exchange_entities_from_event(sender, instance, *args, **kwargs):
    """
    update the exchange servers with connection events
    """
    if instance.event_status not in ['PASS']:
        # only interested in successful events
        return None

    if instance.event_type not in ['connection']:
        # and only connections in this function
        return None

    exchange_server = instance.mail_account.split(',')[1].split('-')[1]

    try:
        exchange_server = ExchangeServer.objects.get(
            exchange_server=exchange_server)
    except ExchangeServer.DoesNotExist:
        exchange_server = ExchangeServer(exchange_server=exchange_server)

    exchange_server.last_connection = instance.event_registered_on

    return exchange_server


@receiver(post_save, sender=MailBotMessage)
def update_exchange_entities_from_message(sender, instance, *args, **kwargs):
    """
    update exchange entitities state from send or receive events
    """
    if instance.event.event_status not in ['PASS']:
        return None

    if instance.event.event_type not in ['send', 'receive']:
        return None

    exchange_server, database = instance.event.mail_account.split(',')[1].\
        split('-')[1:3]
    database = database.split('@')[0]
    last_updated_from_node_id = instance.event.source_host.orion_id

    try:
        exchange_server = ExchangeServer.objects.get(
            exchange_server=exchange_server)
    except ExchangeServer.DoesNotExist:
        exchange_server = ExchangeServer(exchange_server=exchange_server)
        exchange_server.save()

    exchange_server.last_updated_from_node_id = last_updated_from_node_id

    if instance.event.event_type in ['send']:
        exchange_server.last_send = instance.event.event_registered_on
        exchange_server.save()

        return exchange_server, instance.event.event_type

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

    return database, instance.event.event_type

# pylint: enable=unused-argument
