Mail Collector Alerts
=====================

Currently all alerts are delivered via email. There are inactive hooks
available if one wants to deliver alerts via an Orion server.

Each alert evaluation and delivery process is asynchronous and it is executed
via independent `Celery <https://docs.celeryproject.org/en/latest/index.html>`_
`workers <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_. 

All email alerts can be fully disabled at the subscription level.
See :ref:`Mail Collector Subscriptions` for details.

All alerts can be disabled at the :ref:`Mail Collector Subscriptions` level.

All alerts can be disabled at the :ref:`Celery Periodic Tasks` level unless
otherwise specified.



Alerts (and/or warnings) can be raised for the following objects:

* Remote monitoring bots: if a remote bot known to have a running instance
  of the :ref:`Mail Borg Client Application` has not been sending specific
  Windows log event to the :ref:`Mail Collector Application` over a given
  evaluation period, an alert will be raised.thi
  
  The alert threshold, in this case, the evaluation period is configurable
  and it is possible to define multiple alerts of this type with various
  thresholds and various alert levels.
  
  This type of alert can be disabled at the bot definition level. See
  :class:`mail_collector.models.MailHost`. Use the 'enabled' field to
  control this functionality.
  
* Remote monitoring sites: simmilars to above but applying to remote
  monitoring sites.
  
  A remote monitoring site for Exchange services is defined as a remote
  monitoring site with at least one monitoring bot for Exchange services.
  
  These alerts will be raised only if all the bots on a site are
  satisfying the alert thresholds
  
* Exchange server alerts: if, for any known exchange server, a specific
  event type has not been recorded over a given evaluation period, an
  alert will be raised.
  
  The event types tracked for this type of alerts are: connected, sent, and
  received.
  
  This type of alert can be disabled for one or more given Exchange servers
  via the 'enabled' field. See :class:`mail_collector.models.ExchangeServer`
  
* Exchange database alerts: if, for any known Exchange database, an event
  involving database access has not been recorded over a given evaluation
  period, an alert will be raised.
  
  The application is only tracking events of type received for reasons of
  simplicity.
  
  This type of alert can be disabled for one or more given Exchange databases
  via the 'enabled' field. See :class:`mail_collector.models.ExchangeDatabase`
  
* Email services between MX domains alerts: if an email originating from an
  address in a given MX domain (i.e. @phsa.ca) cannot be delivered to an
  address in a given MX domain (i.e. @hssbc.ca) and assuming that the
  application is aware that such functionality is supported over a given
  evaluation period, an alert will be raised.
  
  We track this functionality via the
  :class:`mail_collector.models.MailBetweenDomains` model by recording
  timepstamps for interactions between pairs of MX domains.
  
  This type of alert can be disabled for any pair of MX domains using the
  'enabled` field of the :class:`mail_collector.models.MailBetweenDomains`
  model
  
* Failed Exchange event alert: if an Exchange event of any type with a status
  of FAILED is detected, an alert will be raised.
  
  This type of alert cannot be disabled at the :ref:`Celery Periodic Tasks`
  level
