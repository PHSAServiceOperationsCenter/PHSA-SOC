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
:ref:`Mail Collector Subscriptions` for details.

Reports for email services between domains
------------------------------------------

* `Report MX domain pairs for which email delivery services are broken 
  <../../../admin/django_celery_beat/periodictask/?q=Exchange+report+failed+email+verification+between+domains>`_
  
* `Report email delivery services status for all MX domain pairs 
  <../../../admin/django_celery_beat/periodictask/?q=Exchange+report+all+email+verification+between+domains>`_

Reports for Exchange ``send`` and ``receive`` events
----------------------------------------------------

Reports about Exchange servers
------------------------------

Reports about Exchange databases
--------------------------------
