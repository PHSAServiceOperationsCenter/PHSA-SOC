"""
.. _copy_custom_props:

copy custom properties between orion servers

:module:    p_soc_auto.orion_flash.orion.copy_custom_props

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Feb. 20, 2019

"""
from .api import src_props, dst_props, create_props

QRY_CUSTOM_PROPS = (
    'SELECT Field, DataType, MaxLength, StorageMethod,'
    ' Description, TargetEntity, Mandatory, Default, DisplayName,'
    ' Uri, InstanceSiteId FROM Orion.CustomProperty'
)
ENT_CUSTOM_PROPS = 'Orion.NodesCustomProperties'
VERB_CUSTOM_PROPS = 'CreateCustomProperty'


def copy_custom_props(entity=ENT_CUSTOM_PROPS, verb=VERB_CUSTOM_PROPS,
                      src_props=src_props(qry=QRY_CUSTOM_PROPS),
                      dst_props=dst_props(qry=QRY_CUSTOM_PROPS)):
    copy_props = []
    _ = [
        copy_props.append(src_prop) for src_prop in src_props
        if src_prop['Field'] not in
        [dst_prop['Field'] for dst_prop in dst_props]
    ]

    return create_props(entity, verb, src_props)
