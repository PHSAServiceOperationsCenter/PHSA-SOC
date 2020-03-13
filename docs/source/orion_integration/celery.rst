`Celery` Considerations for the `Orion Integration Application`
===============================================================

Orion Integration Celery Queues
-------------------------------

The `Celery queues and exchanges 
<https://docs.celeryproject.org/en/latest/userguide/routing.html#exchanges-queues-and-routing-keys>`_
are defined respectively under the :attr:`p_soc_auto.settings.CELERY_QUEUES`
setting and under the :attr:`p_soc_auto.settings.CELERY_EXCHANGES` setting.

The `orion` queue is dedicated to handling all the tasks for the
:ref:`Orion Integration Application`. See :mod:`orion_integration.tasks`.

Orion Integration Celery Workers
--------------------------------

The :ref:`Orion Integration Application` is using two dedicated `Celery
<https://docs.celeryproject.org/en/latest/index.html>`__
`worker <https://docs.celeryproject.org/en/latest/userguide/workers.html>`__.

See :ref:`Celery Worker Configuration` for more details about configuring and
daemonizing `Celery workers` and :ref:`The phsa_celery_mail_collector.service file`
for more details about running such `workers`.

PHSA Automation Celery Worker Service for Orion Integration Tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This service is running all the `Celery worker processes` used by the
:ref:`Orion Integration Application`.

The configuration files for this service are under source control under the
`configs/celery` directory.

Here is the service definition file:

.. literalinclude:: ../../../configs/celery/phsa_celery_orion.service
   :language: cfg
   
Here is the `worker` configuration file:

.. literalinclude:: ../../../configs/celery/phsa_celery_orion.conf
   :language: cfg
