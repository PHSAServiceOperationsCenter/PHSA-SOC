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
)

# pylint: disable=unused-argument


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
        # only interested in successful events
        return None

    if instance.event.event_type not in ['send', 'receive']:
        return None

    exchange_server, database = instance.event.mail_account.split(',')[1].\
        split('-')[1:3]
    database = database.split('@')[0]

    try:
        exchange_server = ExchangeServer.objects.get(
            exchange_server=exchange_server)
    except ExchangeServer.DoesNotExist:
        exchange_server = ExchangeServer(exchange_server=exchange_server)
        exchange_server.save()

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

    database.save()

    return database, instance.event.event_type

# pylint: enable=unused-argument
