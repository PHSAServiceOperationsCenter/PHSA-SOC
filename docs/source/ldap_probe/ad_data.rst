Network Nodes Providing AD Services
===================================

The :ref:`Active Directory Services Monitoring Application` is using two
data sources for information about network nodes that provide such services.

.. _nonorionadnodes:

The internal data source
------------------------

This data source is internal to the application and is modeled by the
:class:`ldap_probe.models.NonOrionADNode` model.

The application will monitor the data in the model above for entries that
duplicate information provided by the :ref:`Orion Nodes` source based on
the `IP` address of the network node. Such entries will be removed
automatically.
The schedule for the task executing this operation is available as
`AD controller monitoring: remove duplicate AD nodes` from the `periodic tasks
configuration page </../../../admin/django_celery_beat/periodictask/`__.

Other than that, it is the duty of the `SOC` operators to maintain this
data source.

.. _orionadnodes:

Orion Nodes
-----------

This data source is based on using the `Orion` server. The data source is
described by the :class:`ldap_probe.models.OrionADNode`. The data is
maintained indirectly by the :ref:`Orion Integration Application`.
