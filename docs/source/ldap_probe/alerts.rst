`AD` Services Alerts
====================

`AD` Services Error Alert
-------------------------

These alerts are raised if an `LDAP` probe cannot connect to an `AD` services
node. The node being down or in the process of rebooting is the most common
cause for such an event.

 

`AD` Services Performance Alerts
--------------------------------

`AD` Services Network Nodes Alerts
----------------------------------

The conditions for triggering these alerts will be evaluated on a daily
basis.

These alerts are not directly related to the quality of the `AD` services
available on the `PHSA` networks but to the quality of the data sources
that inform this application about the network nodes providing `AD` services.

`AD` controller nodes not defined in Orion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

These are nodes for which network information is not available in Orion.

`AD` controller nodes mis-defined in Orion
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Some of these nodes show multiple times in Orion with different node captions,
e.g. `node1-short-name-wmi` and `node-short-name-snmp`.

Some of these nodes do not have a `DNS` property in Orion.