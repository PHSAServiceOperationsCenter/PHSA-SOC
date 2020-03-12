Citrus Borg Reports
===================

Currently all reports are delivered via email.

Each report evaluation and delivery process is asynchronous and it is executed
via independent `Celery workers
<https://docs.celeryproject.org/en/latest/userguide/workers.html>`_.

All email reports can be fully disabled at the subscription level.
See :ref:`Subscription Services` for details.

All reports can be disabled from the `Citrus Borg periodic tasks admin page 
<../../../admin/django_celery_beat/periodictask>`_ unless otherwise specified.

Logon summary report
--------------------

A report with the event `state` counts per hour for events generated over a
configurable interval will be emailed periodically.

* This report is executed using the schedule defined at `logon summary report
  <../../../admin/django_celery_beat/periodictask/?q=logon+summary+report>`__
  
* This report is evaluating events over the interval defined at
  `Ignore events created older than
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ignore_events_older_than>`__
  
* This report uses the subscription at `Citrix logon event summary
  <../../../admin/ssl_cert_tracker/subscription/?q=Citrix+logon+event+summary>`__
  to render the emails
