Mail Collector Celery Details
=============================

Celery Data Collection Considerations
-------------------------------------

The mail borg events from all the bots are centralized via the Logstash
server and queued to the RabbitMQ server via the **logstash** exchange.
There is a **logstash** queue bound to that exchange and the Mail Collector
application is pulling in the events from that queue. See 
:ref:`Data Collection` for more details.

Celery Queues
-------------

The `Celery queues and exchanges 
<https://docs.celeryproject.org/en/latest/userguide/routing.html#exchanges-queues-and-routing-keys>`_
are defined respectively under the :attr:`p_soc_auto.settings.CELERY_QUEUES`
setting and under the :attr:`p_soc_auto.settings.CELERY_EXCHANGES` setting.

The `mail_collector` queue is dedicated for all the :ref:`tasks` used by the
:ref:`Mail Collector Application`.

Celery Worker Configuration
---------------------------

We are using a dedicated 
`Celery <https://docs.celeryproject.org/en/latest/index.html>`_
`worker <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_ to
service all the :ref:`tasks` used by the :ref:`Mail Collector Application`.

This service is 
`daemonized <https://docs.celeryproject.org/en/latest/userguide/daemonizing.html>`_ 
to run as a 
`systemd service <https://www.freedesktop.org/wiki/Software/systemd/>`_.

The `systemd <https://www.freedesktop.org/wiki/Software/systemd/>`_
configuration files are provided under the project directory in
:file:`configs/celery/`.

The phsa_celery_mail_collector.service file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This is the systemd service file. It needs to symlinked or copied to the
:file:`/etc/systemd/system` directory depending on the Linux distribution running on
the host.
Here are the steps and/or alternate steps to enable and run the
phsa_celery_mail_collector service:

1. make sure there is no listing for this file under :file:`/etc/systemd/system`

2. enable the service by opening a shell on the host and executing:
   
   .. code-block:: bash

      [root@lvmsocq02 ~]# systemctl enable /opt/phsa/p_soc_auto/configs/celery/phsa_celery_mail_collector.service
    
3. if the above command fails, symlink the file under :file:`/etc/systemd/system`
   and try again to enable the service:
    
   .. code-block:: bash

      [root@lvmsocq02 ~]# cd /etc/systemd/system
      [root@lvmsocq02 ~]# ln -fs /opt/phsa/p_soc_auto/configs/celery/phsa_celery_mail_collector.service
      [root@lvmsocq02 ~]# systemctl enable phsa_celery_mail_collector.service
    
4. if the enable command still fails, copy the file to the
   :file:`/etc/systemd/system` directory and enable the service

5. start the service:

   .. code-block:: bash
    
      [root@lvmsocq02 ~]# systemctl start phsa_celery_mail_collector.service
    
We prefer to avoid copying files to system directories if possible. This way
any changes to :file:`foo.service` files will become active without having to
worry about copying files over.

Here is the content of this file:

.. literalinclude:: ../../../configs/celery/phsa_celery_mail_collector.service
   :language: cfg
   
The most relevant details in this file show that:

* we are using the fork mechanism for starting multiple intances of this
  process
  
* the process belongs to a dedicated system user

* the procees is using the `celery multi start 
  <http://docs.celeryproject.org/en/latest/userguide/workers.html#restarting-the-worker>`_
  command to start/restart the process(es)
  
* the stop command will allows the process to terminate cleanly

The :file:`phsa_celery_mail_collector.conf` file
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This file is used to configure the :file:`phsa_celery_mail_collector.service`
`systemd service <https://www.freedesktop.org/wiki/Software/systemd/>`_.

This files resides under the :file:`p_soc_auto\\configs\\celery` directory. No
special OS level steps are required under the current runtime configuration.

Here is the content of this file:

.. literalinclude:: ../../../configs/celery/phsa_celery_mail_collector.conf
   :language: cfg

The most relevant details in this file:

* the :literal:`--queues` value shows that this process will serve only
  `Celery task 
  <https://docs.celeryproject.org/en/latest/userguide/tasks.html>`_ that
  explicitly use the 'mail_collector' queue
  
* the :literal:`--autoscale` value shows that this process autoscales

* the :literal:`--soft-time-limit` value will cause tasks to time out with
  an :exc:`celery.exceptions.SoftTimeLimitException` exception. Our code is
  currently not catching this exception

Optimizing task execution for the :ref:`Mail Collector Application`
-------------------------------------------------------------------

The heaviest tasks for this application are related to functionality described
in :ref:`Mail Collector Data Collection`.

Under steady-state, with the current default configuration, each
:ref:`Mail Borg Client Application` instance will send 294 events spread
over a period of approximately 20 minutes every hour
to the :ref:`Mail Collector Application` and each event will trigger a
separate instance of the :meth:`mail_collector.tasks.store_mail_data` task.

This translates to a load of 0.25 tasks/sec for each bot that runs a
:ref:`Mail Borg Client Application` instance. The worst case scenario will
assume that all bots are running a :ref:`Mail Borg Client Application`
instance and that all mail check operations will execute at the same time.
There are currently 14 active bots and the load under the worst case scenarion
will be 3.43 tasks/sec.

Considering that the worker described above autoscales up to a 100 instances
and that the :meth:`mail_collector.tasks.store_mail_data` task is rate limited
to 5 tasks/sec, there is no risk of worker failure at steady-state.

However, we have noticed problems if, for operational reasons, the
worker service will go down. The most common cause for such failures is that
the file system(s) on the host will run out of space.
When this happens, the events will be queued at various levels in the system
and the worker will be subject to an avalanche of events to process that will
overwhelm our current configuration.

There are 2 solutions to resolve this situation:

* increase the autoscaling factor for the celery worker service(s) before
  restarting them. This will avoid loss of data and will not require any
  changes in the `RabbitMQ exchange configuration 
  <https://www.rabbitmq.com/>`_. The downside to this approach is that all the
  alerts and reports that could not be sent while the workes were down are
  also queued and they will be send out after the workers are restarted which
  will result in a lot of emails being sent out in a very short oeriod of time
  
* wipe out the message store of the `RabbitMQ server 
  <https://www.rabbitmq.com/>`_. This is a destructive procedure that will
  result in data loss. Additionally we will have to manually bind the
  ``logstash`` queue to the ``logstash`` exchange on the `RabbitMQ server 
  <https://www.rabbitmq.com/>`_. this procedure is described under
  :ref:`RabbitMQ Server`
