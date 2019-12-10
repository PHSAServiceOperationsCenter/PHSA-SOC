Mail Collector Data Collection
==============================

Data Collection
---------------

Instances of the :ref:`Mail Borg Client Application` running on monitoring
bots located at remote sites are generating data about Exchange services
availability for each remote site in the form of Windows event log entries.
The Windows events thus generated are collected via a chain composed of
`Winlogbeat <https://www.elastic.co/products/beats/winlogbeat>`_, 
`Logstash <https://www.elastic.co/products/logstash>`_,
and `RabbitMQ <https://www.rabbitmq.com/>`_ and delivered to the
:ref:`Mail Collector Application`.

:Note:

        There is a version restriction for both Winlogbeat and Logstash. We
        only support version 6.5.4 for both products.

The data collection process is asynchronous and it is executed via
independent `Celery <https://docs.celeryproject.org/en/latest/index.html>`_
`workers <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_.

The data collection functionality is partially shared with the
:ref:`Citrus Borg Application`. The common module is a consumer of AMQP
messages that integrates with 
`Celery <https://docs.celeryproject.org/en/latest/index.html>`_
`workers <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_.
This module is implemented using the
`celery-message-consumer package
<https://github.com/depop/celery-message-consumer>`_. See the
:mod:`citrus_borg.consumers` module for detail.

The `Celery task <https://docs.celeryproject.org/en/latest/userguide/tasks.html>`_
responsible for data collection in this application is
:meth:`mail_collector.tasks.store_mail_data`.

Data Retention
--------------

From an operational perspective, the data collected by this application is
only relevant for short periods of time.

The application accounts for this fact by providing functionality to expire
collected data via the 'is_expired' field of the 
:class:`mail_collector.models.MailBotLogEvent` model. Expired events will
not be taken into consideration when evaluating any alert conditions described
under :ref:`Mail Collector Alerts` or when populating any reports described
under :ref:`Mail Collector Reports`.

It is also possible to delete expired events.

Events are expired and/or deleted by the
:meth:`mail_collector.tasks.expire_events` `Celery 
<https://docs.celeryproject.org/en/latest/index.html>`_ task using the
:ref:`Expire Exchange events`  and :ref:`Delete expired Exchange events`
dynamic settings.

Event expiration for the :ref:`Mail Collector Application` is scheduled to
execute from the `Expire collected mail messages periodic task 
<../../../admin/django_celery_beat/periodictask/?q=&task=mail_collector.tasks.expire_events>`_.

See `Celery Periodic Tasks 
<http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html>`_ and
`Using custom scheduler classes 
<http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#using-custom-scheduler-classes>`_
for more details about scheduling `Celery 
<https://docs.celeryproject.org/en/latest/index.html>`_ tasks.
