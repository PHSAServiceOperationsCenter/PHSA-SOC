SSL Certificates Tracker Celery Details
=======================================

SSL Celery Queues
-----------------

See :ref:`Celery Queues` for details about `Celery` `queues` and `exchanges`.

The :ref:`SSL Certificate Tracker Application` uses:

* The `ssl` queue for sending out `SSL` alerts and reports

* The `shared` queue for tasks that spawn other tasks

* The `nmap` queue for tasks that will run `NMAP` scans

SSL Celery Worker Configuration
-------------------------------

See :ref:`Celery Worker Configuration` for explanations about `Celery` `workers`.
Also see :ref:`monkey_with_systemd` for details about interacting with `Celery`
`worker` system services.

All the configuration files for the `Celery` `workers` used by the :ref:`SSL
Certificate Tracker Application` are under source control in the
`configs/celery/` directory.

The PHSA Automation Celery Worker Service for SSL Certificates Tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../../configs/celery/phsa_celery_ssl.service
   :language: cfg

.. literalinclude:: ../../../configs/celery/phsa_celery_ssl.conf
   :language: cfg

The PHSA Automation Celery Worker Service for Shared Tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../../configs/celery/phsa_celery_shared.service
   :language: cfg

.. literalinclude:: ../../../configs/celery/phsa_celery_shared.conf
   :language: cfg

The PHSA Automation Celery Worker Service for Nmap Tasks
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. literalinclude:: ../../../configs/celery/phsa_celery_nmap.service
   :language: cfg

.. literalinclude:: ../../../configs/celery/phsa_celery_nmap.conf
   :language: cfg

