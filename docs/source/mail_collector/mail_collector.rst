Mail Collector Application
==========================

The Mail Collector application is responsible for generating alerts for
email and Exchange functionality.

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



.. toctree::
   :maxdepth: 2
   
   settings.rst
   dynamic_settings.rst
   mail_collector_subscriptions.rst
   celery.rst
   modules.rst
   
