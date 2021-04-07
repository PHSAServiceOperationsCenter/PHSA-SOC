"""
.. _consumers:

Consumers Module
----------------

:module:    citrus_borg.consumers

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

This module contains functions and classes that allow a `Django Celery
<https://docs.celeryproject.org/en/latest/django/first-steps-with-django"""\
""".html#using-celery-with-django>`__
to consume `AMQP  <https://www.amqp.org/>`__ messages emanating from arbitrary
sources.

See :ref:`Logstash Server` for a discussion about the source of the `AMQP
<https://www.amqp.org/>`__ messages.

The data collection architecture is described in :ref:`Mail Collector Data
Collection`. This module is shared between the :ref:`Citrus Borg Application`
and the :ref:`Mail Collector Application`.

This module uses the `celery-message-consumer
<https://github.com/depop/celery-message-consumer>`__ package.

"""
import json
from logging import getLogger

from event_consumer import message_handler

from citrus_borg.preferences import get_list_preference
from mail_collector.tasks import store_mail_data

from .models import AllowedEventSource
from .tasks import process_citrix_login

LOG = getLogger(__name__)


@message_handler('logstash', exchange='default')
def process_win_event(body):
    """
    consume `Windows` log events delivered as `AMQP` messages

    This function is a callback that gets invoked every time there is a new
    message placed on the `logstash` `RabbitMQ <https://www.rabbitmq.com/>`__
    `exchange`.

    See `Routing Tasks
    <https://docs.celeryproject.org/en/latest/userguide/routing.html>`__ in the
    `Celery` docs for a primer on `exchanges` and `queues`.

    :arg str body: the message to be consumed

        It is a string because the :ref:`WinlogBeat Service` event collectors
        and the :ref:`Logstash Server` are configured to encode `Windows` log
        events as plain text

    """
    LOG.debug('Processing %s', body)

    borg = json.loads(body)
    source_name = borg.get('source_name', None)
    if source_name not in list(
            AllowedEventSource.objects.values_list('source_name', flat=True)):
        LOG.info('%s is not a monitored event source', source_name)
        return

    if source_name in get_list_preference('citrusborgevents__source'):
        process_citrix_login.delay(borg)
    elif source_name in get_list_preference('exchange__source'):
        store_mail_data.delay(borg)
