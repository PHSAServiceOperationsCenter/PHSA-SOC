"""
.. _qv:

queries and verbs for Orion SDK

:module:    p_soc_auto.orion_flash.orion.qv

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
ALL_CUSTOM_PROPS_QUERY = (
    'SELECT Table, Field, DataType, MaxLength, StorageMethod,'
    ' Description, TargetEntity, Mandatory, Default, DisplayName,'
    ' Uri, InstanceSiteId '
    'FROM Orion.CustomProperty'
)
FILTERED_CUSTOM_PROPS_QUERY = (
    'SELECT Table, Field, DataType, MaxLength, StorageMethod,'
    ' Description, TargetEntity, Mandatory, Default, DisplayName,'
    ' Uri, InstanceSiteId '
    'FROM Orion.CustomProperty '
    'WHERE Table=@table AND Field=@field'
)
CUSTOM_PROPS_VERB = 'CreateCustomProperty'
CUSTOM_PROPS_VALS_VERB = 'CreateCustomPropertyWithValues'
CUSTOM_PROPS_INVOKE_ARGS = [
    'Field', 'Description', 'DataType', 'MaxLength', 'ValidRange', 'Parser',
    'Header', 'Alignment', 'Format', 'Units', 'Usages', 'Mandatory', 'Default',
]
CUSTOM_PROPS_VALS_INVOKE_ARGS = [
    'Field', 'Description', 'DataType', 'MaxLength', 'ValidRange', 'Parser',
    'Header', 'Alignment', 'Format', 'Units', 'Values', 'Usages', 'Mandatory',
    'Default',
]
VALUES_FOR_CUSTOM_PROP_QUERY = (
    'SELECT Value '
    'FROM Orion.CustomPropertyValues '
    'WHERE Table=@table AND Field=@field'
)
NODE_PROPS_QUERY = (
    'SELECT Caption, NodeDescription, Description, DNS, SysName, Vendor, '
    'Location, Contact, CustomStatus, IOSImage, IOSVersion '
    'FROM Orion.Nodes '
    'WHERE IPAddress=@ipaddress')
NODE_URI_QUERY = (
    'SELECT Uri '
    'FROM Orion.Nodes '
    'WHERE IPAddress=@ipaddress')
NODE_URI_BY_NAME_QUERY = (
    'SELECT Uri '
    'FROM Orion.Nodes '
    'WHERE Caption=@name')
ALL_NODES_IPADDRESS_QUERY = ('SELECT IPAddress FROM Orion.Nodes')
NODE_CUSTOM_PROPS_QUERY = (
    'SELECT ons.NodeID, ons.IPAddress,'
    ' oncp.Address, oncp.Building, oncp.City, oncp.Closet, oncp.Comments,'
    ' oncp.DeviceType, oncp.HA, oncp.HardwareIncidentStatus,'
    ' oncp.IncidentStatus, oncp.Make, oncp.NodeOwner, oncp.OutOfBand,'
    ' oncp.ProgramApplication, oncp.ProgramApplicationType,'
    ' oncp.Provider, oncp.Region, oncp.Site, oncp.SiteContactName,'
    ' oncp.SiteHours, oncp.SitePhone, oncp.SiteType,'
    ' oncp.WANbandwidth, oncp.WANnode, oncp.WANProvider'
    ' FROM Orion.Nodes(nolock=true) ons'
    ' LEFT JOIN Orion.NodesCustomProperties(nolock=true) oncp'
    ' on ons.NodeID = oncp.NodeID'
    ' WHERE ons.IPAddress=@ipaddress'
)
