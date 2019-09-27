Logstash Server
===============

The `Logstash <https://www.elastic.co/products/beats/winlogbeat>`_ server is
an off-the-shelf component of the :ref:`SOC Automation Project`. `Logstash` is
owned and developed by `Elastic <https://www.elastic.co/about/>`_ who also
own and develop `ElasticSearch <https://www.elastic.co/products/elasticsearch>`_.

The `Logstash <https://www.elastic.co/products/beats/winlogbeat>`_ acts as a
feeding mechanism for `ElasticSearch <https://www.elastic.co/products/elasticsearch>`_.
However, it has been developed using a plug-in based architecture and it can
be used to feed data into many different storage mechanisms.

At the other end, `Logstash <https://www.elastic.co/products/beats/winlogbeat>`_
collects and concentrates data from various system sources.

In our case, `Logstash <https://www.elastic.co/products/beats/winlogbeat>`_
collects Windows lo events data from remote monitoring bots, and delivers
said data to the :ref:`RabbitMQ Server` over the `AMPQ
<https://www.amqp.org/>`_ protocol.

The data collection is executed using another product owned and developed by
`Elastic <https://www.elastic.co/about/>`_, namely `Winlogbeat
<https://www.elastic.co/products/beats/winlogbeat>`_.

:Note:

        There is a version restriction for both Winlogbeat and Logstash. We
        only support version 6.5.4 for both products.

.. todo::

    Upgrade both the remote bots and the :ref:`SOC Automation Server` with
    the latest versions of these products.
    
`Logstash <https://www.elastic.co/products/beats/winlogbeat>`_ server is using
the `Rabbitmq output plugin
<https://www.elastic.co/guide/en/logstash-versioned-plugins/current/v5.1.1-plugins-outputs-rabbitmq.html>`_
to communicate with the :ref:`RabbitMQ Server`.

Logstash configuration
----------------------

For the `Logstash <https://www.elastic.co/products/beats/winlogbeat>`_ server
itself, we are using the default configuration as created by the installation
process.

The `Rabbitmq output plugin
<https://www.elastic.co/guide/en/logstash-versioned-plugins/current/v5.1.1-plugins-outputs-rabbitmq.html>`_
is configured via the source controlled file ``configs/logstash/rabbitmq.conf``.

.. literalinclude:: ../../../configs/logstash/rabbitmq.conf
   

Symlink or copy this file to ``/etc/logstash/conf.d/``.

Logstash security
-----------------

At a minimum, we need to change the values for the `user` and `password` keys
in this configuration file.

The `Rabbitmq output plugin
<https://www.elastic.co/guide/en/logstash-versioned-plugins/current/v5.1.1-plugins-outputs-rabbitmq.html>`_
does support `SSL`.
Enabling `SSL` between `Logstash` and `RabbitMQ` should happen at the same time
as the effort for :ref:`Celery security`.