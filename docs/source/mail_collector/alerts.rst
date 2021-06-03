Mail Collector Alerts
=====================

Currently all alerts are delivered via email. There are inactive hooks
available if one wants to deliver alerts via an Orion server.

Each alert evaluation and delivery process is asynchronous and it is executed
via independent `Celery <https://docs.celeryproject.org/en/latest/index.html>`_
`workers <https://docs.celeryproject.org/en/latest/userguide/workers.html>`_. 

All email alerts can be fully disabled at the subscription level.
See :ref:`Subscription Services` for details.

All alerts can be disabled from the `Mail Collector periodic tasks admin page 
<../../../admin/django_celery_beat/periodictask>`_ unless otherwise specified.

Alerts for remote monitoring bots
---------------------------------

If a remote bot known to have a running instance of the 
`Mail Collector Application <https://github.com/PHSAServiceOperationsCenter/MailBorg>`__ has not been sending specific Windows log
events to the :ref:`Mail Collector Application` over a given evaluation period,
an alert will be raised.
  
The alert threshold, in this case, the evaluation period is configurable
and it is possible to define multiple alerts of this type with various
thresholds and various alert levels.
  
This type of alert can be disabled at the bot definition level. See
:class:`mail_collector.models.MailHost`. Use the ``enabled`` field to
control this functionality.

**Currently defined:**

* `Critical alert for exchange client bots 
  <../../../admin/django_celery_beat/periodictask/?q=raise+critical+alert+for+exchange+client+bots>`_
  
  The alert condition will be evaluated based on the ``Schedule`` section
  shown on the page linked above.
  
  The threshold for this alert is configured from the dynamic preference at
  `Exchange Client Bot Errors After 
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=bot_error>`_.
  
* `Warning alert for exchange client bots 
  <../../../admin/django_celery_beat/periodictask/?q=raise+warning+alert+for+exchange+client+bots>`_
  
  The threshold for this alert is configured from the dynamic preference at
  `Exchange Client Bot Warnings After 
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=bot_warn>`_
  
:Note:

    The alert thresholds above are shared with other alerts. One must exercise
    caution before one will change them.

These alerts are using the email subscription defined at the
`Exchange Client Bots Not Seen subscription listed here 
<../../../admin/ssl_cert_tracker/subscription/>`_.
  
Alerts for remote monitoring sites
----------------------------------

These alerts are similar to above but applying to remote monitoring sites.
  
A remote monitoring site for Exchange services is defined as a remote
monitoring site with at least one monitoring bot for Exchange services.
  
These alerts will be raised only if all the bots on a site are satisfying
the alert thresholds.

This type of alert can be disabled at the bot definition level. See
:class:`mail_collector.models.MailSite`. Use the ``enabled`` field to
control this functionality.

**Currently defined:**

* `Critical alert for exchange client sites 
  <../../../admin/django_celery_beat/periodictask/?q=raise+critical+alert+for+exchange+client+sites>`_
  
  The threshold for this alert is configured from the dynamic preference at
  `Exchange Client Bot Errors After 
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=bot_error>`_
  
* `Warning alert for exchange client sites 
  <../../../admin/django_celery_beat/periodictask/?q=raise+warning+alert+for+exchange+client+sites>`_
  
  The threshold for this alert is configured from the dynamic preference at
  `Exchange Client Bot Warnings After 
  <../../../admin/dynamic_preferences/globalpreferencemodel/?q=bot_warn>`_

These alerts are using the email subscription defined at the
`Exchange Client Bot Sites Not Seen subscription listed here 
<../../../admin/ssl_cert_tracker/subscription/>`_.
  
Alerts for Exchange servers
---------------------------

if, for any known exchange server, a specific event type has not been recorded
over a given evaluation period, an alert will be raised.
  
The event types tracked for this type of alerts are: ``connected``, ``sent``,
and ``received``.
  
This type of alert can be disabled for one or more given Exchange servers
via the ``enabled`` field. See :class:`mail_collector.models.ExchangeServer`.

**Currently defined:**

* `Critical Exchange server receive alert 
  <../../../admin/django_celery_beat/periodictask/?q=Raise+critical+alert+for+receive+to+exchange+servers>`_
  
  This alert is using the email subscription defined at the
  `Exchange Servers No Receive subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `Critical Exchange server send alert 
  <../../../admin/django_celery_beat/periodictask/?q=Raise+critical+alert+for+send+to+exchange+servers>`_

  This alert is using the email subscription defined at the
  `Exchange Servers No Send subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `Critical Exchange server connection alert
  <../../../admin/django_celery_beat/periodictask/?q=Raise+critical+alert+for+connections+to+exchange+servers>`_
  
  This alert is using the email subscription defined at the
  `Exchange Servers No Connect subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_

* `Warning Exchange server receive alert 
  <../../../admin/django_celery_beat/periodictask/?q=Raise+warning+alert+for+receive+to+exchange+servers>`_
  
  This alert is using the email subscription defined at the
  `Exchange Servers No Receive subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `Warning Exchange server send alert
  <../../../admin/django_celery_beat/periodictask/?q=Raise+warning+alert+for+send+to+exchange+servers>`_

  This alert is using the email subscription defined at the
  `Exchange Servers No Send subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `Warning Exchange server connection alert 
  <../../../admin/django_celery_beat/periodictask/?q=Raise+warning+alert+for+connections+to+exchange+servers>`_
  
  This alert is using the email subscription defined at the
  `Exchange Servers No Connect subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_

* `Warning Exchange server not seen alert
  <../../../admin/django_celery_beat/periodictask/?q=Raise+warning+alert+for+any+exchange+servers>`_
  
  This alert is using the email subscription defined at the
  `Exchange Servers Not Seen subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `Critical Exchange server not seen alert
  <../../../admin/django_celery_beat/periodictask/?q=Raise+critical++alert+for+any+exchange+servers>`_
  
  This alert is using the email subscription defined at the
  `Exchange Servers Not Seen subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_

The threshold for the critical alerts is configured via the dynamic preference at
`Exchange Server Error After 
<../../../admin/dynamic_preferences/globalpreferencemodel/?q=server_error>`_.

The threshold for the warning alerts is configured via the dynamic preference at
`Exchange Server Warning After 
<../../../admin/dynamic_preferences/globalpreferencemodel/?q=server_warn>`_.

Alerts for Exchange databases
-----------------------------

If, for any known Exchange database, an event involving database access has
not been recorded over a given evaluation period, an alert will be raised.
  
The application is only tracking events of type ``received`` for reasons of
simplicity.
  
This type of alert can be disabled for one or more given Exchange databases
via the ``enabled`` field. See :class:`mail_collector.models.ExchangeDatabase`.

**Currently defined:**

* `Critical Exchange database alert 
  <../../../admin/django_celery_beat/periodictask/?q=raise+critical+alert+for+exchange+databases>`_
  
* `Warning Exchange database alert 
  <../../../admin/django_celery_beat/periodictask/?q=raise+warning+alert+for+exchange+databases>`_

These alerts are using the email subscription defined at the
`Exchange Databases Not Seen subscription listed here 
<../../../admin/ssl_cert_tracker/subscription/>`_.
  
These alerts use the same thresholds as the ones defined in the 
:ref:`Alerts for Exchange servers` section.
  
Alerts for email services between MX domains
--------------------------------------------

If an email originating from an address in a given MX domain (i.e. @phsa.ca)
cannot be delivered to an address in a given MX domain (i.e. @hssbc.ca)
and assuming that the application is aware that such functionality is supported
over a given evaluation period, an alert will be raised.

If an email verifying the services between a pair of MX domains has not been
detected for a specific interval, an alert will be raised.
  
We track this functionality via the 
:class:`mail_collector.models.MailBetweenDomains` model by recording
time stamps for interactions between pairs of MX domains.
  
This type of alert can be disabled for any pair of MX domains using the
'enabled` field of the :class:`mail_collector.models.MailBetweenDomains`
model.

**Currently defined:**

* `Critical email between domains verification failure alert 
  <../../../admin/django_celery_beat/periodictask/?q=raise+critical+alert+for+email+check+failure>`_
  
  This alert is using the email subscription defined at the
  `Mail Verification Failed subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_
  
* `Critical email between domains not verified alert 
  <../../../admin/django_celery_beat/periodictask/?q=raise+critical+alert+for+email+check+not+checked>`_
  
  This alert is using the email subscription defined at the
  `Mail Unchecked On Site subscription listed here 
  <../../../admin/ssl_cert_tracker/subscription/>`_.
  
  The threshold for this alarm is the same as the one described in
  :ref:`Alerts for remote monitoring bots` section for critical alerts 
  
Alerts for failed Exchange events
---------------------------------

If an Exchange event of any type with a status of ``FAILED`` is detected,
an alert will be raised.
  
This type of alert is not based on periodically re-evaluating the error
condition. Therefore it cannot be disabled from the
`Mail Collector periodic tasks admin page 
<../../../admin/django_celery_beat/periodictask>`_.

This alert is using the email subscription defined at the
`Exchange Client Error subscription listed here 
<../../../admin/ssl_cert_tracker/subscription/>`_.

Alerts for client bot configuration
-----------------------------------

When a remote bot running an Exchange client instance is sending events
without site information is detected on the server an alert will be raised for
said bot.

This can happen in either of the following cases:

* A bot is not known to the server:
 
  Under normal conditions bot information will only be made
  available on the automation server the first time Windows log events
  originating from said bot are being detected and saved to the server side
  database.
  
  However, even when this is the first time the bot is running, it will still
  query the server for the main configuration needed by the
  `Mail Collector Application <https://github.com/PHSAServiceOperationsCenter/MailBorg>`__ instance. The server will return a special
  `Host doesn't exist <../../../admin/mail_collector/mailhost/?q=host.not.exist>`_ 
  configuration. When this configuration is used, the bot information will
  be created on the server but without valid ``Site`` information.
  
  The server considers this to be an error condition and this type of alert
  is raised to inform the operator that the ``site`` field must be configured
  for the newly detected bot
  
* A bot is known to the server but the ``site`` field has not been configured

* A bot has been running using main configuration data cached locally but the
  operator has changed the ``site`` info in this configuration to something
  the server is not aware of
  
This alert is evaluated periodically as configured in the *Schedule*
section of the `Site not configured on bot Exchange alert 
<../../../admin/django_celery_beat/periodictask/?q=exchange+alert+site+not+configured>`_
page.

This alert is using the email subscription defined at the
`Exchange bot no site subscription listed here 
<../../../admin/ssl_cert_tracker/subscription/>`_.