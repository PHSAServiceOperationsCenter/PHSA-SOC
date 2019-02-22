"""
.. _qv:

queries and verbs for Orion SDK

:module:    p_soc_auto.orion_flash.orion.qv

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Feb. 22, 2019

"""
CUSTOM_PROPS_QUERY = (
    'SELECT Table, Field, DataType, MaxLength, StorageMethod,'
    ' Description, TargetEntity, Mandatory, Default, DisplayName,'
    ' Uri, InstanceSiteId FROM Orion.CustomProperty'
)
CUSTOM_PROPS_VERB = 'CreateCustomProperty'
CUSTOM_PROPS_INVOKE_ARGS = [
    'Field', 'Description', 'DataType', 'MaxLength', 'ValidRange', 'Parser',
    'Header', 'Alignment', 'Format', 'Units', 'Usages', 'Mandatory', 'Default',
]
