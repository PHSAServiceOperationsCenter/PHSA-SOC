SSL Certificate Tracker Application
===================================

The SSL Certificate Tracker Application is responsible for monitoring
expiration and trust for `SSL server certificates
<https://en.wikipedia.org/wiki/Public_key_certificate#TLS/SSL_server_certificate>`_
deployed on various `Cerner CST` network nodes.

The list of monitored network nodes is maintained by the `SolarWinds Orion
<https://www.solarwinds.com/solutions/orion>`_ server. The :ref:`SSL
Certificate Tracker Application` is aware of this list by way of the
:ref:`Orion Integration Application`.

Using a configurable schedule, the SSL Certificate Tracker Application
executes `NMAP <https://nmap.org/>`_ scans for `SSL` certificates against each
network node in the monitored list. Each `NMAP <https://nmap.org/>`_ scan runs
independently and asynchronously. Data collected by the `NMAP
<https://nmap.org/>`_ scans is maintained by the :ref:`SSL Certificate
Tracker Application` in the database.

The `SSL` certificate data is analyzed periodically for validity and trust
information. If problems with these two items are detected, email based
alerts will be raised.

The :ref:`SSL Certificate Tracker Application` is also sending periodic reports
about the state of the known `SSL` certificates.


.. toctree::
   :maxdepth: 2
   
   alerts.rst
   reports.rst
   settings.rst
   dynamic_settings.rst
   celery.rst
   modules.rst
