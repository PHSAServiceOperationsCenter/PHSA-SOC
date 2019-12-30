`AD` Services Monitoring Reports
================================

These reports contain a list of `AD` probes that were executed against all
known and enabled `AD` nodes over a configurable interval.

The reporting interval is configurable via the user preference `Time Interval
To Use When Generating Ldap Reports
</../../../admin/dynamic_preferences/globalpreferencemodel/?q=ldap_reports_period>`__.
Currently, this is set to the default value of 1 hour.

These reports are split between :ref:`AD nodes defined in Orion <orionadnodes>`
and :ref:`AD nodes defined outside Orion <nonorionadnodes>`.

Periodic Summary
----------------

This report lists the results of all the `AD` probes executed during the
configured interval summarized as follows:

* Number of failed probes

* Total number of executed probes

* Average response time for the probe initialization for successful probes

  This is not a very significant number because this operation does not
  require any network traffic
  
* Minimum, average, and maximum response for the 
  :ref:`bind and search <bind_and_search>` or for the 
  :ref:`anonymous bind and read root DSE <anon_bind_and_search>` operations
  for successful probes
  
  .. note::
  
    There are separate reports for :ref:`bind and search
    <bind_and_search>` and :ref:`anonymous bind and read root DSE
    <anon_bind_and_search>` probes.
    
These are periodic summary reports:

* :ref:`Full probe data <bind_and_search>` from :ref:`Orion AD nodes
  <orionadnodes>`:
  
  * scheduled from the `AD controller monitoring: summary report, full bind,
    orion` entry on the `periodic tasks configuration page
    </../../../admin/django_celery_beat/periodictask/>`__
    
  * rendered using the `LDAP: summary report, full bind, orion` subscription
    from the `LDAP subscriptions summary page
    </../../../admin/ssl_cert_tracker/subscription/?q=LDAP%3A>`__

* :ref:`Anonymous probe data <anon_bind_and_search>` from :ref:`Orion AD nodes
  <orionadnodes>`:
  
  * scheduled from the `AD controller monitoring: summary report, anon bind,
    orion` entry on the `periodic tasks configuration page
    </../../../admin/django_celery_beat/periodictask/>`__
    
  * rendered using the `LDAP: summary report, anonymous bind, orion`
    subscription from the `LDAP subscriptions summary page
    </../../../admin/ssl_cert_tracker/subscription/?q=LDAP%3A>`__

* :ref:`Full probe data <bind_and_search>` from :ref:`Non Orion AD nodes
  <nonorionadnodes>`:
  
  * scheduled from the `AD controller monitoring: summary report, full bind,
    non orion` entry on the `periodic tasks configuration page
    </../../../admin/django_celery_beat/periodictask/>`__
    
  * rendered using the `LDAP: summary report, full bind, non orion`
    subscription from the `LDAP subscriptions summary page
    </../../../admin/ssl_cert_tracker/subscription/?q=LDAP%3A>`__

* :ref:`Anonymous probe data <anon_bind_and_search>` from :ref:`Non Orion AD
  nodes <nonorionadnodes>`:
  
  * scheduled from the `AD controller monitoring: summary report, anon bind,
    non orion` entry on the `periodic tasks configuration page
    </../../../admin/django_celery_beat/periodictask/>`__
    
  * rendered using the `LDAP: summary report, anonymous bind, non orion`
    subscription from the `LDAP subscriptions summary page
    </../../../admin/ssl_cert_tracker/subscription/?q=LDAP%3A>`__


Periodic Summary for Error Events
---------------------------------

These are reports with a listing of all failed `AD` probes. These reports do
not provide any summarizations.

* :ref:`AD` probe errors for :ref:`Orion AD nodes <orionadnodes>` and 
  :ref:`Non Orion AD nodes <nonorionadnodes>`:

  * scheduled from the `AD controller monitoring: error summary report` entry
    on the `periodic tasks configuration page
    </../../../admin/django_celery_beat/periodictask/>`__
    
  * rendered using the `LDAP: error report` subscription
    from the `LDAP subscriptions summary page
    </../../../admin/ssl_cert_tracker/subscription/?q=LDAP%3A>`__


Periodic Summary for Performance Degradation Events
---------------------------------------------------

These reports are based on :ref:`periodic summary reports <Periodic Summary>`
but filtered on response times measured by the `AD` probe.

Currently all these reports are scheduled to execute from a single periodic
task configurable from the `AD controller monitoring: performance degradation reports
</../../../admin/django_celery_beat/periodictask/?q=performance+degradation+reports>`__
page.

The reports are segregated by location (see :ref:`Acceptable Performance
Buckets`), by the origin of the definition of the `AD` node (see :ref:`Network
Nodes Providing AD Services`), by the `bind` case (see :ref:`AD Services
Monitoring Using LDAP`), and by the performance degradation level (see
:ref:`Performance Degradation Levels`).

Acceptable Performance Buckets
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

The definition of what is considered to be **acceptable performance** is based
on the location of the `AD` node; what is considered acceptable for a node
located in the Cerner data center in Ontario will not be acceptable for a
node located in the Kamloops data center.

The performance buckets (locations) are defined in the
:class:`ldap_probe.models.ADNodePerfBucket` model and can be maintained from
the `Performance Groups for ADS Nodes
</../../../admin/ldap_probe/adnodeperfbucket/>`__ page.

It is the responsibility of the SOC operator to maintain the acceptable
performance data and to asign the `AD` nodes to their respective performance
buckets.

Performance Degradation Levels
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Currently, the application is generating reports for multiple degradation
levels. These levels are expressed as typical log levels and the threshold
for each level is configured on a per location basis in the
:class:`ldap_probe.models.ADNodePerfBucket` model as follows:

* INFO:
  
  Will measure performance degradation against the threshold
  defined by the value of the
  :attr:`ldap_probe.models.ADNodePerfBucket.avg_warn_threshold`
  attribute of the :class:`ldap_probe.models.ADNodePerfBucket` instance
  to which the `AD` node belongs.
  
  This threshold is considered against average reponse times

* WARNING:

  Uses the value of the
  :attr:`ldap_probe.models.ADNodePerfBucket.avg_err_threshold`.
  
  This threshold is also considered against average reponse times

* ERROR:
  
  Uses the value of the
  :attr:`ldap_probe.models.ADNodePerfBucket.alert_threshold`.
  
  This threshold is considered against maximum reponse times
  
See the documentation for :meth:`ldap_probe.tasks.dispatch_ldap_perf_reports`
for details on how to disable performance degradation reports for one or more
levels.

Email subcriptions for performance degradation reports
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All the email subscriptions used for these reports are defined on the
`LDAP subscriptions performance degradation reports summary page
</../../../admin/ssl_cert_tracker/subscription/?q=degrade>`__.

The subscriptions for `ERROR` level reports are identifiable by the suffix
`err`.

`AD` Services Network Nodes Reports
===================================

These reports are not directly related to the quality of the `AD` services
available on the `PHSA` networks but to the quality of the data sources
that inform this application about the network nodes providing `AD` services.

These reports are generated and dispatched periodically using a configurable
schedule.

`AD` controller nodes not defined in Orion
------------------------------------------

These are `AD` nodes for which network information is not available in Orion.
Such node are defined under `Domain Controllers not present in Orion
</../../../admin/ldap_probe/nonorionadnode/>`__ and the information on that
page must be maintained manually.

We consider it desirable that the definitions for such `AD` nodes be created
in Orion and, in order to facilitate such an operation, we are providing a
periodic report with said `AD` nodes.

The report is being dispatched via email using the `LDAP: non Orion AD nodes
<../../../admin/ssl_cert_tracker/subscription/?q=LDAP%3A+non+Orion+AD+nodes>`__
email subscription.

The task that generates and executed this report is scheduled by the
`AD controller monitoring: non Orion AD nodes report` periodic task which can be
configured from the `periodic tasks configuration page
</../../../admin/django_celery_beat/periodictask/>`__.

`AD` controller nodes incorrectly defined in Orion
--------------------------------------------------

There are several `AD` nodes that are defined on the `Orion` server but the
information available there is not suitable or incomplete.

All the `AD` nodes that are subject to these reports must be defined as
`domain controllers` on the `Orion` server.


Nodes with no DNS name information
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These are `AD` nodes defined on the `Orion` server for which the `DNS` `Orion`
property is not set.

The report tracking such nodes is executed automatically using the 
`AD controller monitoring: FQDN Orion AD nodes report` periodic task
scheduled from the `periodic tasks configuration page
</../../../admin/django_celery_beat/periodictask/>`__.

The report is dispatched via email using the `LDAP: Orion FQDN AD nodes
</../../../admin/ssl_cert_tracker/subscription/?q=LDAP%3A+Orion+FQDN+AD+nodes>`__
email subscription.
 

Duplicate nodes
^^^^^^^^^^^^^^^

A subset of the `AD` nodes from above can be (and at least one **is**)
duplicates from an `IP address` perspective. That is absolutely not a correct
`Orion` node definition.

The report tracking such nodes is executed automatically using the 
`AD controller monitoring: Duplicate Orion AD nodes report` periodic task
scheduled from the `periodic tasks configuration page
</../../../admin/django_celery_beat/periodictask/>`__.

The report is dispatched via email using the `LDAP: Duplicate Orion AD nodes
</../../../admin/ssl_cert_tracker/subscription/?q=LDAP%3A+Duplicate+Orion+AD+nodes>`__
email subscription.



Orion DNS name not on DNS server
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. todo::

    See `<https://trello.com/c/Y2gHblhU>`__.