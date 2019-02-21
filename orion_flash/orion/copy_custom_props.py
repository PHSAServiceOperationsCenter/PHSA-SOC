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
import requests

from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from orionsdk import SwisClient

from django.conf import settings

from citrus_borg.dynamic_preferences_registry import get_preference

QRY_CUSTOM_PROPS = (
    'SELECT Table, Field, DataType, MaxLength, StorageMethod,'
    ' Description, TargetEntity, Mandatory, Default FROM Orion.CustomProperty'
)


def get_session():
    """
    prepare and return a :class:`<requests.Session>` instance with all the
    trimmings
    """
    session = requests.Session()

    session.timeout = (get_preference('orionserverconn__orion_conn_timeout'),
                       get_preference('orionserverconn__orion_read_timeout'))
    session.verify = get_preference('orionserverconn__orion_verify_ssl_cert')

    retry = Retry(
        total=get_preference('orionserverconn__orion_retry'),
        read=get_preference('orionserverconn__orion_retry'),
        connect=get_preference('orionserverconn__orion_retry'),
        backoff_factor=get_preference('orionserverconn__orion_backoff_factor'),
        status_forcelist=(500, 502, 504))

    adapter = HTTPAdapter(max_retries=retry)

    session.mount('http://', adapter)
    session.mount('https:/', adapter)

    return session


def get_props(host, user, password, qry):
    return SwisClient(
        host, user, password,
        verify=get_preference('orionserverconn__orion_verify_ssl_cert')).\
        query(qry).get('results')


SRC_CUSTOM_PROPS = get_props(
    settings.ORION_HOSTNAME, settings.ORION_USER, settings.ORION_PASSWORD, QRY_CUSTOM_PROPS)

DST_CUSTOM_PROPS = get_props(
    '10.248.211.70',
    # get_preference('orionservercon__orion_hostname'),
    get_preference('orionserverconn__orion_user'),
    get_preference('orionserverconn__orion_password'), QRY_CUSTOM_PROPS)

mopy_props = []


def copy_custom_props(dst, src_props, dst_props):
    copy_props = []
    _ = [
        copy_props.append(src_prop) for src_prop in src_props
        if (src_prop['Table'], src_prop['Field']) not in
        [(dst_prop['Table'], dst_prop['Field']) for dst_prop in dst_props]
    ]
