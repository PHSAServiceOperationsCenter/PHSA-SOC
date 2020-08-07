.. SOC_Automation documentation master file, created by
   sphinx-quickstart on Tue Aug 27 14:59:18 2019.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

PHSA SOC Automation Documentation
=================================

The SOC Automation project plans, implements, and maintains custom network
and system monitoring software for the SOC.

The SOC Automation project provides the following facilities:

* **Custom Data Collection Facilities**:
  There are multiple components for collecting custom monitoring data.
  Some data collection components are not location dependent and  can be run from
  the SOC Automation server. Other data collection components rely on local network
  architecture, and must be executed on machines located at remote sites.
  
* **Custom Alert Facilities**:
  All the data collected is stored and analyzed on the SOC Automation server.
  Configurable alerts are generated based on this analysis and dispatched via
  email to interested parties. In-depth analysis can be requested from the SOC
  but data is only stored for three days due to space limitations.

* **Alert Integration with the Current Monitoring Infrastructure**:
  The team is currently planning and developing integrating alerts/data generated
  by the SOC automation components with other monitoring platforms, including Orion,
  and Power BI.

 
SOC Automation Server Infrastructure
------------------------------------

.. toctree::
   :maxdepth: 2
   :caption: SOC Automation Server Infrastructure:

   p_soc_auto/p_soc_auto.rst
   p_soc_auto_base/p_soc_auto_base.rst
   p_soc_auto_base/email_services.rst
   p_soc_auto_base/subscriptions.rst
   
SOC Automation Server Applications
----------------------------------

.. toctree::
   :maxdepth: 2
   :caption: SOC Automation Server Applications:

   citrus_borg/citrus_borg.rst
   ldap_probe/ldap_probe.rst
   mail_collector/mail_collector.rst
   orion_integration/orion_integration.rst
   sftp/sftp.rst
   ssl_cert_tracker/ssl_cert_tracker.rst

   
SOC Automation Client Applications
----------------------------------

.. toctree::
   :maxdepth: 2
   :caption: SOC Automation Client Applications:

   mail_borg/mail_borg.rst
   

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
