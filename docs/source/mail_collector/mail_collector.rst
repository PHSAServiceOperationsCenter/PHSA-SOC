Mail Collector Application
==========================

The :ref:`Mail Collector Application` is responsible for collecting Windows
log events created by instances of the
:ref:`Mail Borg Client Application` running on remote monitoring bots, and
for generating alerts and warnings with regards to  email and Exchange services
availability at remote sites.

The application will also generate periodic reports with regards to  email
and Exchange services availability at remote sites.

The application is also capable of analyzing the availability of all and/or
various Exchange servers and Exchange databases based on the configurations
made available to the :ref:`Mail Borg Client Application` instances. 

This application is also responsible for providing main configurations for 
nstances of the :ref:`Mail Borg Client Application` running on remote
monitoring bots.


  

.. toctree::
   :maxdepth: 2
   
   data_collection.rst
   alerts.rst
   reports.rst
   settings.rst
   dynamic_settings.rst
   mail_collector_subscriptions.rst
   celery.rst
   modules.rst
   
