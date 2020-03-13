Citrus Borg Celery Considerations
=================================

Data collection for the :ref:`Citrus Borg Application` is very similar to the
:ref:`Mail Collector Application`. See :ref:`Celery Data Collection Considerations`
for more details.

Citrus Borg Celery Queues
-------------------------

The `Celery queues and exchanges 
<https://docs.celeryproject.org/en/latest/userguide/routing.html#exchanges-queues-and-routing-keys>`_
are defined respectively under the :attr:`p_soc_auto.settings.CELERY_QUEUES`
setting and under the :attr:`p_soc_auto.settings.CELERY_EXCHANGES` setting.

The `citrus_borg` queue is dedicated to handling all event maintenance tasks.

The `borg_chat` queue is dedicated to handling all alert and reporting tasks.

Citrus Borg Celery Workers
--------------------------

The :ref:`Citrus Borg Application` is using two dedicated `Celery worker
<https://docs.celeryproject.org/en/latest/userguide/workers.html>`__.

See :ref:`Celery Worker Configuration` for more details about configuring and
daemonizing `Celery workers` and :ref:`The phsa_celery_mail_collector.service file`
for more details about running such `workers`.

PHSA Automation Celery Worker Service for Citrus Borg Assimilation Tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This service is running `Celery worker processes` used for event maintenance tasks
over the `citrus_borg` queue.

The configuration files for this service are under source control under the
`configs/celery` directory.

Here is the service definition file:

.. literalinclude:: ../../../configs/celery/phsa_celery_citrus_borg.service
   :language: cfg
   
Here is the `worker` configuration file:

.. literalinclude:: ../../../configs/celery/phsa_celery_citrus_borg.conf
   :language: cfg
   
PHSA Automation Celery Worker Service for Citrus Borg Indoctrination Tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

This service is running `Celery worker processes` used for alerts and reporting
tasks over the `borg_chat` queue.

The configuration files for this service are under source control under the
`configs/celery` directory.

Here is the service definition file:

.. literalinclude:: ../../../configs/celery/phsa_celery_borg_chat.service
   :language: cfg
   
Here is the `worker` configuration file:

.. literalinclude:: ../../../configs/celery/phsa_celery_borg_chat.conf
   :language: cfg
   