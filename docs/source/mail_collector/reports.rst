Mail Collector Reports
======================

Currently all reports are delivered via email. Each email delivering a report
will also have an attachment in comma separated format with all the data from
said report in tabular format.

All reports are delivered as scheduled individually from specific pages
available via the `Mail Collector periodic tasks listing page 
<../../../admin/django_celery_beat/periodictask>`_.

Delivery for all reports can be disabled via the
`Mail Collector periodic tasks listing page 
<../../../admin/django_celery_beat/periodictask>`_.

Delivery for all reports can be disabled at the subscription level. See
:ref:`Subscription Services` for details.

Reports for email services between domains
------------------------------------------

* `Report MX domain pairs for which email delivery services are broken 
  <../../../admin/django_celery_beat/periodictask/?q=Exchange+report+failed+email+verification+between+domains>`_
  
  This report use the email subscription defined at the
  `Mail Verification Report subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `Report email delivery services status for all MX domain pairs 
  <../../../admin/django_celery_beat/periodictask/?q=Exchange+report+all+email+verification+between+domains>`_
  
  This report use the email subscription defined at the
  `Mail Verification Report subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `Exchange report verification not executed 
  <../../../admin/django_celery_beat/periodictask/?q=Exchange+report+verification+not+executed>`_
  
  This report is returning a list of MX domain pairs for which the age of the
  last email check is greater than a duration defined by the dynamic preference
  at `Exchange reporting interval 
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=report_interval>`_.
  
  This report uses the email subscription defined at the
  `Exchange Send Receive By Site subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
Reports for Exchange ``send`` and ``receive`` events
----------------------------------------------------

* `Reports for Exchange send and receive events aggregated by bot  
  <../../../admin/django_celery_beat/periodictask/?q=Exchange+send+receive+by+bot>`_

  For each known and enabled Exchange bot, email a list of successfull send and
  receive events, and a list of failed send and receive events.

  
  The full report uses the email subscription defined at the
  `Exchange Send Receive By Site subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_.
  
  The failures only report uses the email subscription defined at the
  `Exchange Failed Send Receive By Site subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `Reports for Exchange send and receive events aggregated by site 
  <../../../admin/django_celery_beat/periodictask/?q=Exchange+send+receive+by+site>`_
  
  For each known and enabled Exchange site, email a list of successfull send and
  receive events, and a list of failed send and receive events.
  
  The full report uses the email subscription defined at the
  `Exchange Send Receive By Site subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_.
  
  The failures only report uses the email subscription defined at the
  `Exchange Failed Send Receive By Site subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_

Report generation is configured in the ``Schedule`` section of the pages
linked above.

The error level of the reports is configured  from the dynamic preference at
`Exchange report level 
<../../../admin/dynamic_preferences/globalpreferencemodel/?q=report_level>`_.

The report interval is configured from the dynamic preference at
`Exchange reporting interval 
<../../../admin/dynamic_preferences/globalpreferencemodel/?q=report_interval>`_

Reports about Exchange servers
------------------------------

* `No receive exchange servers report 
  <../../../admin/django_celery_beat/periodictask/?q=No+receive+exchange+servers+report>`_
  
  This report is returning a list of Exchange servers that have not serviced
  any Exchange receive requests over a duration greater than the one defined by
  the dynamic preference at `Exchange reporting interval 
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=report_interval>`_.
  
  This report uses the email subscription defined at the
  `Exchange Servers No Receive subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `No send exchange servers report 
  <../../../admin/django_celery_beat/periodictask/?q=No+send+exchange+servers+report>`_
    
  This report is returning a list of Exchange servers that have not serviced
  any Exchange send requests over a duration greater than the one defined by
  the dynamic preference at `Exchange reporting interval 
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=report_interval>`_.
  
  This report uses the email subscription defined at the
  `Exchange Servers No Send subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `No connect exchange servers report 
  <../../../admin/django_celery_beat/periodictask/?q=No+connect+exchange+servers+report>`_
  
  This report is returning a list of Exchange servers that have not serviced
  any Exchange connection requests over a duration greater than the one defined by
  the dynamic preference at `Exchange reporting interval 
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=report_interval>`_.
  
  This report uses the email subscription defined at the
  `Exchange Servers No Connection subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `Dead exchange servers report 
  <../../../admin/django_celery_beat/periodictask/?q=Dead+exchange+servers+report>`_
  
  This report is returning a list of Exchange servers that have not serviced
  any Exchange requests over a duration greater than the one defined by
  the dynamic preference at `Exchange reporting interval 
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=report_interval>`_.
  
  This report uses the email subscription defined at the
  `Exchange Servers Not Seen subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
Reports about Exchange databases
--------------------------------

* `Dead echange databases report 
  <../../../admin/django_celery_beat/periodictask/?q=Dead+exchange+databases+report>`_
  
  This report is returning a list of Exchange databases that have not serviced
  any Exchange request over a duration greater than the one defined by the
  dynamic preference at `Exchange reporting interval 
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=report_interval>`_.
  
  This report uses the email subscription defined at the
  `Exchange Databases Not Seen subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_