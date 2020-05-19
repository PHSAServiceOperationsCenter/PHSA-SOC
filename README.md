PHSA SOC Automation
===================

The SOC Automation project copyright is held by the 
[Provincial Health Services Authority of British Columbia](http://www.phsa.ca/).

The SOC Automation project is an effort of the Service Operations Center team (SOC).

The SOC Automation project plans, implements, and maintains custom network
and system monitoring software for the SOC.

The SOC Automation project provides the following:

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
  
Docs notes
----------

Documentation is generated and hosted locally.

The docs build directory is exposed as an alias on the server host where the
SOC Automation project is running as per the configs/nginx/nginx.conf file.

It is the responsibility of the developer to rebuild the documentation.
  
Mail Collector Application
--------------------------

The ``Mail Collector Application`` is responsible for collecting Windows
log events created by instances of the ``Mail Borg Client Application``
running on remote monitoring bots, and for generating alerts with regards 
to email and Exchange service availability at remote sites.

The application is also capable of analyzing the availability of all and/or
various Exchange servers and Exchange databases based on the configurations
made available to the :ref:`Mail Borg Client Application` instances. 

This application is also responsible for providing main configurations for 
instances of the ``Mail Borg Client Application`` running on remote
monitoring bots.

Active Directory Services Monitoring Application
------------------------------------------------

This application is monitoring network nodes that provide 
[Active Directory Domain Services](https://docs.microsoft.com/en-us/windows-server/identity/ad-ds/get-started/virtual-dc/active-directory-domain-services-overview])
(AD).


The application is collecting monitoring data by way of sending periodic
[LDAP](https://ldap.com/) connection requests to each network node known
to be an **AD** controller.
