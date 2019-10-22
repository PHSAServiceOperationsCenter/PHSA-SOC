Citrus Borg Alerts
==================

Currently all alerts are delivered via email. There is an inactive application
available if one wants to deliver alerts via an Orion server.

Each alert evaluation and delivery process is asynchronous and it is executed
via independent `Celery <https://docs.celeryproject.org/en/latest/index.html>`_
`workers <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_. 

All email alerts can be fully disabled at the subscription level.
See :ref:`Subscription Services` for details.

All alerts can be disabled from the `Citrus Borg periodic tasks admin page 
<../../../admin/django_celery_beat/periodictask>`_ unless otherwise specified.

Citrus Borg bot alerts
----------------------

Bot not working
^^^^^^^^^^^^^^^

If a `ControlUp` instance on a remote bot has not sent any events over a
configurable interval, the bot is considered to be down and an alert will be
raised.

**Currently defined:**

* Scheduled from

* Evalutation interval

Bot logons are failing
^^^^^^^^^^^^^^^^^^^^^^

Citrix response times are below acceptable levels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Citrus Borg remote site alerts
------------------------------

Citrus Borg Citrix session host alerts
--------------------------------------

If a `Citrix` session host known to the system has not serviced any requests
over a configurable interval, an alert will be raised.

**Currently defined:**

* Scheduled from

* Evaluation interval configured from

Citrus Borg `Orion` integration
-------------------------------

If the `orion_flash` application is
activated, bot related alerts will also be visible on an `Orion` server for bots
that are defined as `Orion` nodes.

.. todo::

    Document the `orion_flash` application.


