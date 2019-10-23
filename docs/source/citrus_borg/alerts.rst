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

* `Dead Citrix monitoring bots alert
  <http://10.2.50.35:8080/admin/django_celery_beat/periodictask/?q=Dead+Citrix+monitoring+bots+alert>`__

* Evalutation interval configured from `Bot Not Seen Alert Threshold
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=dead_bot_after>`__

* Subscription: `Dead Citrix monitoring bots
  <../../../admin/ssl_cert_tracker/subscription/?q=Dead+Citrix+monitoring+bots>`__

Bot logons are failing
^^^^^^^^^^^^^^^^^^^^^^

If a `ControlUp` instance on a remote bot reports more failed `Citrix` logon events
than a configurable threshold over a configurable interval, an alert will be
raised. E.G. a bot detects 2 failed logons over 10 minutes.

* `Citrix failed logon alerts
  <../../../admin/django_celery_beat/periodictask/?q=Citrix+failed+logon+alerts>`-_
  
* `Failed Logon Events Count Alert Threshold
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=logon_alert_threshold>`__

* `Failed Logons Alert Interval
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=logon_alert_after>`__

* Subscription: `Citrix logon alert
  <../../../admin/ssl_cert_tracker/subscription/?q=Citrix+logon+alert>`__

Citrix response times are below acceptable levels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a `ControlUp` instance on a remote bot is reporting `Citrix` response times
less than the threshold, an alert will be raised. The response times are
averaged over a configurable interval.

* `Citrix alert: user response time
  <../../../admin/django_celery_beat/periodictask/?q=Citrix+alert%3A+user+response+time>`__

* `Maximum Acceptable Response Time For Citrix Events
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ux_alert_threshold>`__

* `Alert Monitoring Interval For Citrix Events
  <../../..//admin/dynamic_preferences/globalpreferencemodel/?q=ux_alert_interval>`__

* Subscription: `Citrix UX Alert
  <../../../admin/ssl_cert_tracker/subscription/?q=Citrix+UX+Alert>`__

Citrus Borg remote site alerts
------------------------------

Sites where all the bots are down
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If all the `ControlUp` bots at a remote site are down, raise an alert.

* `Dead Citrix client sites alert
  <../../../admin/django_celery_beat/periodictask/?q=Dead+Citrix+client+sites+alert>`__

* `Site Not Seen Alert Threshold
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=dead_site_after>`__

* Subscription: `Dead Citrix client sites
  <../../../admin/ssl_cert_tracker/subscription/?q=Dead+Citrix+client+sites>`__

Citrus Borg Citrix session host alerts
--------------------------------------

If a `Citrix` session host known to the system has not serviced any requests
over a configurable interval, an alert will be raised.

* `Dead Citrix farm hosts alert
  <../../../admin/django_celery_beat/periodictask/?q=Dead+Citrix+farm+hosts+alert>`__

* `Reporting Period For Dead Nodes
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=node_forgotten_after>`__

* Subscription: `Missing Citrix farm hosts
  <../../../admin/ssl_cert_tracker/subscription/?q=Missing+Citrix+farm+hosts>`__

Citrus Borg `Orion` integration
-------------------------------

If the `orion_flash` application is
activated, bot related alerts will also be visible on an `Orion` server if the bot
that is the subject of the alarm is defined as `Orion` nodes.

.. todo::

    Document the `orion_flash` application.


