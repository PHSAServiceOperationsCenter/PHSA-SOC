`AD` Services Alerts
====================

`AD` Services Error Alert
-------------------------

These alerts are raised if an `LDAP` probe cannot connect to an `AD` services
node. The node being down or in the process of rebooting is the most common
cause for such an event.

Such alerts have no configurable parameters. They can be disabled on a per
`AD` node basis; if an `AD` node is disabled on the `Domain Controllers from
Orion <../../../admin/ldap_probe/orionadnode/>`__ page or on the `Domain
Controllers not present in Orion
</../../../admin/ldap_probe/nonorionadnode/>`__ page.

These alerts are dispatched via email using the `LDAP: error alerts
subscription
</../../../admin/ssl_cert_tracker/subscription/?q=LDAP%3A+error+alerts+subscription>`__.

`AD` Services Performance Alerts
--------------------------------

These alerts are raised if the response time of a request made against an
`AD` services node is larger than a specific threshold.

.. _perf_subs:

These alerts are dispatched via email using the `LDAP: Performance alerts
subscription
</../../../admin/ssl_cert_tracker/subscription/?q=LDAP%3A+Performance+alerts+subscription>`__.

There are currently two levels of performance alerts and the `response time
threshold` is configurable for both levels.

.. _perf_err:

* `ERROR` performance alerts with the threshold configurable via the `Ldap
  Performance Alert Threshold (In Seconds)
  </../../../admin/dynamic_preferences/globalpreferencemodel/?q=ldap_perf_alert>`__
  global preference. Currently this threshold is set to its default value of
  0.500 seconds
  
.. _perf_warn:

* `WARNING` performance alerts with the threshold configurable via the `Ldap
  Performance Warning Threshold (In Seconds)
  </../../../admin/dynamic_preferences/globalpreferencemodel/?q=ldap_perf_warn>`__
  global preference. Currently this threshold is set to 0.200 seconds. Its
  default value is 0.100 seconds
  
.. note::

    The name of the email subscription for performance alerts is also
    configurable as a global preference from `Email Subscription For Ldap
    Performance Alerts
    </../../../admin/dynamic_preferences/globalpreferencemodel/?q=ldap_perf_subscription>`__.
    
    The :ref:`LDAP: Performance alerts subscription <perf_subs>` will have to
    be changed accordingly. 