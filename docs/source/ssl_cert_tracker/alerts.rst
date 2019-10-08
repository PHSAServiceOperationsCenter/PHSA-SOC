SSL Certificate Tracker Alerts
==============================

The alerts that can be raised by the :ref:`SSL Certificate Tracker Application` are
triggered from the `Celery Periodic Tasks` at `SSL certificates reports
<../../../admin/django_celery_beat/periodictask/?q=Email+SSL+Certificates+Report+Daily>`__:

* **SSL certificates that expire in less than 2 days**

* **SSL certificates that expire in less than 7 days**

* **SSL certificates that expire in less than 30 days**

* **SSL certificates that expire in less than 90 days**

All these alerts use the `SSL Report` :class:`Subscription
<ssl_cert_tracker.models.Subscription>`.