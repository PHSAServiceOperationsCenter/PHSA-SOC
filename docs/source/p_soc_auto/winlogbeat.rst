WinlogBeat Service
==================

:Note:

        There is a version restriction for both Winlogbeat and Logstash. We
        only support version 6.5.4 for both products.

`Winlogbeat <https://www.elastic.co/products/beats/winlogbeat>`_ is a
Windows service owned and developed by `Elastic
<https://www.elastic.co/about/>`_.

Within the :ref:`SOC Automation Project`, `Winlogbeat
<https://www.elastic.co/products/beats/winlogbeat>`_ is responsible for
collecting Windows log events from various network nodes an delivering
them to the :ref:`Logstash Server` for further processing.

Currently, each remote bot used for either `Citrix` monitoring, `Exchange`
monitoring, or both is running the `Winlogbeat
<https://www.elastic.co/products/beats/winlogbeat>`_ service.

To install and configure the `Winlogbeat
<https://www.elastic.co/products/beats/winlogbeat>`_ service on a remote bot,
please consult the 
`SOC - Procedural Guide - Handling Emails From the Citrix Monitoring Automation Server
<http://our.healthbc.org/sites/gateway/team/TSCSTHub/_layouts/15/WopiFrame2.aspx?sourcedoc=/sites/gateway/team/TSCSTHub/Shared Documents/Drafts/SOC - Procedural Guide - Handling Emails From the Citrix Monitoring Automation Server.doc&action=default>`_
MOP.

Here is a sample (source-controlled) of the configuration file for
`Winlogbeat <https://www.elastic.co/products/beats/winlogbeat>`_.
The most important setting to be aware of is the address of the logstash server,
under ``output.logstash``.


.. literalinclude:: ../../../configs/winlogbeat/winlogbeat.yml
   :language: yaml
   
Winlogbeat scaling
------------------

The `hosts:` entry in the configuration shown above is a list. The service
will distribute network packets between the `Logstash` servers defined in
that list in a `round-robin` fashion. Note that this has more to do with
scaling the :ref:`Logstash Server`.

Winlogbeat security
-------------------

The `SSL` related entries commented out in the configuration file shown above
suggest that `Winlogbeat
<https://www.elastic.co/products/beats/winlogbeat>`_ supports `SSL`.