"""
.. _consumers:

Consumers Module
----------------

:module:    citrus_borg.consumers

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Oct. 9, 2019

This module contains functions and classes that allow a `Django Celery
<https://docs.celeryproject.org/en/latest/django/first-steps-with-django.html#using-celery-with-django>`__
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

from celery.utils.log import get_task_logger
from event_consumer import message_handler

from citrus_borg.dynamic_preferences_registry import get_preference

_logger = get_task_logger(__name__)  # pylint: disable=invalid-name
"""
:class:`logging.Logger` instance used in this module

.. todo::

    The way this attribute is initialized means that log messages from this
    module will be scattered amongst various celery log files. Maybe it would
    make sense to use a dedicated hard-coded `Django` logger. This way when we
    want to keep track of incoming events, we will not have to chase through
    tens of log files.

"""


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
    from .models import AllowedEventSource
    from .tasks import store_borg_data
    from mail_collector.tasks import store_mail_data

    _logger.debug('resistance is futile... now processing %s' % body)

    borg = json.loads(body)
    if borg.get('source_name', None) not in list(
            AllowedEventSource.objects.values_list('source_name', flat=True)):
        _logger.info('%s is not a monitored event source' %
                     borg.get('source_name', None))
        return

    if borg.get('source_name', None) in \
            get_preference('citrusborgevents__source').split(','):
        store_borg_data.delay(borg)

    elif borg.get('source_name', None) in \
            get_preference('exchange__source').split(','):
        store_mail_data.delay(borg)
