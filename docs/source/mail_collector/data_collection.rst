Mail Collector Data Collection
==============================

Data Collection
---------------

Instances of the :ref:`Mail Borg Client Application` running on monitoring
bots located on remote sites are generating data about Exchange services
availability for each remote site in the form of Windows event log entries.
The Windows events thus generated are collected via a chain composed of
`Winlogbeat <https://www.elastic.co/products/beats/winlogbeat>`_, 
`Logstash <https://www.elastic.co/products/logstash>`_,
and `RabbitMQ <https://www.rabbitmq.com/>`_ and delivered to the
:ref:`Mail Collector Application`.

:note:

        There is a version restriction for both Winlogbeat and Logstash. We
        only support version 6.5.4 for both products.

The data collection process is asynchronous and it is executed via
independent `Celery <https://docs.celeryproject.org/en/latest/index.html>`_
`workers <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_.

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

It is also possible to delete expire events.

Events are expired and/or deleted by the
:function:`mail_collector.tasks.expire_events` based on dynamic settings
defined under
:class:`citrus_borg.dynamic_properties_registry.ExchangeExpireEvents` and
:class:`citrus_borg.dynamic_properties_registry.ExchangeDeleteExpired`.

Event expiration is evaluated and executed as below::

    In [3]: from django_celery_beat.models import PeriodicTask

    In [9]: PeriodicTask.objects.filter(task__iexact='mail_collector.tasks.expire_events').values('name','task','interval__every','interval__period')
    Out[9]: <ExtendedQuerySet [{'name': 'Expire collected mail messages', 'task': 'mail_collector.tasks.expire_events', 'interval__every': 72, 'interval__period': 'hours'}]>

    In [10]:
    
See `Celery Periodic Tasks 
<http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html>`_ and
`Using custom scheduler classes 
<http://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#using-custom-scheduler-classes>`_
