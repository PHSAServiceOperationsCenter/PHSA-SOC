Citrus Borg Reports
===================

Currently all reports are delivered via email.

Each report evaluation and delivery process is asynchronous and it is executed
via independent `Celery <https://docs.celeryproject.org/en/latest/index.html>`_
`workers <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_. 

All email reports can be fully disabled at the subscription level.
See :ref:`Subscription Services` for details.

All reports can be disabled from the `Citrus Borg periodic tasks admin page 
<../../../admin/django_celery_beat/periodictask>`_ unless otherwise specified.

Bots down report
----------------

A report about remote bots that have not sent any `ControlUp` events for a
configurable interval will be emailed periodically.

* This report is executed using the schedule defined at `Dead Citrix client sites report
  <../../../admin/django_celery_beat/periodictask/?q=Dead+Citrix+client+sites+report>`__

* A bot is considered down if it has not sent any events for the interval defimed
  by `Reporting period for dead nodes
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=node_forgotten_after>`__

* This report uses the subscription at `Dead Citrix monitoring bots
  <../../../admin/ssl_cert_tracker/subscription/?q=Dead+Citrix+monitoring+bots>`__
  to render the emails

Sites down report
-----------------

A report about sites where none of the bots have sent any `ControlUp` events over
a configurable interval will be emailed periodically.

* This report is executed using the schedule defined at
  `Dead Citrix client sites report
  <../../../admin/django_celery_beat/periodictask/?q=Dead+Citrix+client+sites+report>`__

* A site is considered down if none of the site bots have sent any events for the
  interval defined by `Reporting period for dead nodes
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=node_forgotten_after>`__

* This report uses the subscription at `Dead Citrix client sites
  <../../../admin/ssl_cert_tracker/subscription/?q=Dead+Citrix+client+sites>`__
  to render the emails

`Citrix` session hosts down report
----------------------------------

A report about `Citrix` session hosts that have not serviced any requests over
a configurbale interval will be emailed periodically.

* This report is executed using the schedule defined at
  `Dead Citrix farm hosts report
  <../../../admin/django_celery_beat/periodictask/?q=Dead+Citrix+farm+hosts+report>`__
  
* A `Citrix` session host is considered down if it has not serviced any requests
  over the interval defined at `Reporting period for dead nodes
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=node_forgotten_after>`__
  
* This report uses the subscription at `Missing Citrix farm hosts
  <../../../admin/ssl_cert_tracker/subscription/?q=Missing+Citrix+farm+hosts>`__
  to render the emails

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

Logon and response times by site and bot reports
------------------------------------------------

A report for each site, bot combination with the event `state` counts per hour
and the event `response times` averaged per hour for events detected over a
configurable interval will be emailed periodically.

* These reports are executed using the schedule defined at
  `Logon Pass/Fail Counts and User Exeprience Metrics Report
  <../../../admin/django_celery_beat/periodictask/?q=Logon+Pass%2FFail+Counts+and+User+Exeprience+Metrics+Report>`__
  
* These reports are eavaluating events generated over the interval defined at
  `User experience reporting period
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ux_reporting_period>`__
  
* These reports use the subscription at `Citrix logon event and ux summary
  <../../../admin/ssl_cert_tracker/subscription/?q=Citrix+logon+event+and+ux+summary>`__
  to render the emails

Failed logons report
--------------------

A report with all the failed `Citrix` events including the failure reason
(as reported by `ControlUp`) over a configurable interval will be emailed
periodically.

* This report is executed using the schedule defined at
  `Email Citrix Failed Logons Report
  <../../../admin/django_celery_beat/periodictask/?q=Email+Citrix+Failed+Logons+Report>`__
  
  .. image:: EmailCitrixFailedLogonReports.png
  
* This reporting is evaluating events generated over the interval defined at
  `Logon Events Reporting Period
  <http://10.2.50.35:8080/admin/dynamic_preferences/globalpreferencemodel/?q=logon_report_period>`__

* These reports use the subscription at `Citrix Failed Logins Report
  <../../../admin/ssl_cert_tracker/subscription/?q=Citrix+Failed+Logins+Report>`__
  to render the emails

Failed response times report
----------------------------

A report with all the unacceptable response times for `Citrix` logon events
collected over a configurable interval will be emailed.

Unacceptable response times are defined as longer that a configurable threshold.

* This report is executed using the schedule defined at
  `Email Citrix Bot Report for Excessive Logon Response Time Events
  <../../../admin/django_celery_beat/periodictask/?q=Email+Citrix+Bot+Report+for+Excessive+Logon+Response+Time+Events>`__
  
* This report is evaluating events collected over the interval defined at
  `User experience reporting period
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ux_reporitng_period>`__
  
* The response time theshold used when generating this report is defined at
  `Maximum acceptable response time for citrix events
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=ux_alert_threshold>`__
  
* This report uses the subscription at `Citrix Failed UX Event Components Report
  <../../../admin/ssl_cert_tracker/subscription/?q=Citrix+Failed+UX+Event+Components+Report>`__
  to render the emails

Failed logons by site and bot reports
-------------------------------------

For each site, bot combination a report with failed logons details and event `state`
counts  calculated using events collected over a configurable interval will be
emailed periodically.

* These reports are executed using the schedule defined at
  `Trigger Emails with Citrix Failed Logons per Site Report
  <../../../admin/django_celery_beat/periodictask/?q=Trigger+Emails+with+Citrix+Failed+Logons+per+Site+Report>`__
  
* These reports are evaluating events collected over the interval defined at
  `Logon events reporting period
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=logon_report_period>`__

* These reports are using the subscription at `Citrix Failed Logins per Report
  <../../../admin/ssl_cert_tracker/subscription/?q=Citrix+Failed+Logins+per+Report>`__
  to render the emails


