Citrus Borg Alerts
==================

Currently all alerts are delivered via email. There is an inactive application
available if one wants to deliver alerts via `Orion
<https://www.solarwinds.com/solutions/orion>`__.

Each alert evaluation and delivery process is asynchronous and it is executed
via independent `Celery workers
<https://docs.celeryproject.org/en/latest/userguide/workers.html>`_.

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
  <../../../admin/django_celery_beat/periodictask/?q=Dead+Citrix+monitoring+bots+alert>`__

* Evaluation interval configured from `Bot Not Seen Alert Threshold
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=dead_bot_after>`__

* Subscription: `Dead Citrix monitoring bots
  <../../../admin/ssl_cert_tracker/subscription/?q=Dead+Citrix+monitoring+bots>`__

Citrix response times are below acceptable levels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

If a `ControlUp` instance on a remote bot is reporting `Citrix` response times
longer than the threshold, an alert will be raised. The response times are
averaged over a configurable interval.

* `Citrix alert: user response time
  <../../../admin/django_celery_beat/periodictask/?q=Citrix+alert%3A+user+response+time>`__

* `Maximum Acceptable Response Time For Citrix Events
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ux_alert_threshold>`__

* `Alert Monitoring Interval For Citrix Events
  <../../..//admin/dynamic_preferences/globalpreferencemodel/?q=ux_alert_interval>`__

* Subscription: `Citrix UX Alert
  <../../../admin/ssl_cert_tracker/subscription/?q=Citrix+UX+Alert>`__

Citrus Borg `Orion` integration
-------------------------------

If the `Orion Flash` application is activated, bot related alerts will also be visible
on an `Orion` server if the bot that is the subject of the alarm is defined as `Orion` nodes.



