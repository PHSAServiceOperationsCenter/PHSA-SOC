Citrus Borg Application
=======================

The :ref:`Citrus Borg Application` is responsible for collecting Windows
log events created by instances of the
`ControlUp` application running on remote monitoring bots. `ControlUp` is a
diagnostic tool for `Citrix` application services and the :ref:`Citrus Borg
Application` is also responsible for generating alerts and warnings with regards to
such application services

The application will also generate periodic reports with regards to the
availability  of `Citrix` application services at remote sites.

For more details about collecting Windows log events, see :ref:`Mail Collector
Data Collection`. In fact these two applications share some of the modules
used for data collection and even some of the models where the collected data
is stored.

The ``subscription`` services used by the :ref:`Citrus Borg Application`
are provided via the :ref:`Subscription Services` component.

The ``email`` services used by the :ref:`Citrus Borg Application`
are provided via the :ref:`Email Services` component.


.. toctree::
   :maxdepth: 2
   
   alerts.rst
   reports.rst
   celery.rst
   modules.rst

