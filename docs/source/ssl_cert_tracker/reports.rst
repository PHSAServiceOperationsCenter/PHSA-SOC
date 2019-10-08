SSL Certificate Tracker Reports
===============================

The reports emailed by the :ref:`SSL Certificate Tracker Application` are
triggered from the `Celery Periodic Tasks` at `SSL certificates reports
<../../../admin/django_celery_beat/periodictask/?q=Email+SSL+Certificates+Report+Daily>`__:

* **Email Invalid SSL Certificates Report Daily**: this can also be considered an
  alert
  
  The subscription for this report is `Invalid SSL Report` and it is available from one of
  the links on this page `<../../../admin/ssl_cert_tracker/subscription/?q=SSL+Report>`__

* **Email Expired SSL Certificates Report Daily**: this can also be considered an
  alert
  
  The subscription for this report is `Expired SSL Report` and it is available from one of
  the links on this page `<../../../admin/ssl_cert_tracker/subscription/?q=SSL+Report>`__

* **Email SSL Certificates Report Daily**

  The subscription for this report is `SSL Report` and it is available from one of
  the links on this page `<../../../admin/ssl_cert_tracker/subscription/?q=SSL+Report>`__
  
 