Mail Borg Client Application
============================

The :ref:`Mail Borg Client Application` is a highly specialized client for
accessing `Exchange Web Services (EWS) 
<https://searchwindowsserver.techtarget.com/definition/Exchange-Web-Services-EWS>`_.
This application is currently restricted to Widows platforms.

The :ref:`Mail Borg Client Application` executes batch email operations via
`Exchange Web Services (EWS) 
<https://searchwindowsserver.techtarget.com/definition/Exchange-Web-Services-EWS>`_.

The results of the email operations are reported as `Windows event log entries 
<https://searchwindowsserver.techtarget.com/definition/Windows-event-log>`_.

The `Winlogbeat <https://www.elastic.co/products/beats/winlogbeat>`_
service is pushing the ``Windows event log entries`` to the
`Logstash <https://www.elastic.co/products/logstash>`_. The
`Logstash <https://www.elastic.co/products/logstash>`_ server collects
``events`` from all the :ref:`Mail Borg Client Application` instances and
pushes them to the ``Celery`` stack described by
:ref:`Mail Collector Celery Details` via the
`RabbitMQ <https://www.rabbitmq.com/>`_ server.

.. toctree::
   :maxdepth: 2
   
   modules.rst
   build.rst