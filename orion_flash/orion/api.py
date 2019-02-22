"""
.. _common:

functions and methods for the orion package

:module:    p_soc_auto.orion_flash.orion.common

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Feb. 21, 2019

"""
import requests

from requests import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry

from orionsdk import SwisClient

from django.conf import settings

from citrus_borg.dynamic_preferences_registry import get_preference

src_defaults = (settings.ORION_HOSTNAME,
                settings.ORION_USER, settings.ORION_PASSWORD)
dst_defaults = ('10.248.211.70',
                # get_preference('orionservercon__orion_hostname'),
                get_preference('orionserverconn__orion_user'),
                get_preference('orionserverconn__orion_password'))

if not settings.ORION_VERIFY_SSL_CERT:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def get_session():
    """
    prepare and return a :class:`<requests.Session>` instance with all the
    trimmings

    #TODO: not useful until the orionsdk package is update =d to version 0.0.8
    or higher
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


def query_props(host, user, password, qry):
    """
    execute a SWSQL query against an Orion Server

    :arg host: the name or ip address of the Orion server

    :arg user: the username of the account used to access the server

    :arg password: the password of the account used to access the server

    :arg str qry: the SWQL query

    :returns: a ``list`` of ``dict``
    """
    return SwisClient(
        host, user, password,
        verify=get_preference('orionserverconn__orion_verify_ssl_cert')).\
        query(qry).get('results')


class SourceSwis():
    """
    wrap around the SwisClient for a cleaner look
    """

    def __init__(self, *args, verify=settings.ORION_VERIFY_SSL_CERT):
        """
        :arg args: (host, user, password) for the orion server

        this is not the cleanest implementation because we are not doing
        any error checking. OTOH, this is not exactly aiming for
        production quality but for expediency

        """
        if not args:
            args = src_defaults
        self.orion_connection = SwisClient(  # pylint: disable=no-value-for-parameter
            *args, verify=verify)

    def query(self, query, **params):
        """
        call the SwisClient query method and return just the results
        """
        return self.orion_connection.query(query, **params).get('results')


class DestSwis(SourceSwis):
    def __init__(
            self, *args,
            verify=get_preference('orionserverconn__orion_verify_ssl_cert')):
        if not args:
            args = dst_defaults

        super().__init__(*args, verify)

    def create_custom_property(
            self, src_props, entity='Orion.NodesCustomProperties'):
        pass


def create_props(entity, verb, props, host=None, user=None, password=None):
    results = []

    if host is None:
        host = dst_defaults[0]

    if user is None:
        user = dst_defaults[1]

    if password is None:
        password = dst_defaults[2]

    swis_client = SwisClient(
        host, user, password,
        verify=get_preference('orionserverconn__orion_verify_ssl_cert')
    )

    for prop in props:
        #results.append(swis_client.create(entity, **prop))
        try:
            res = swis_client.invoke(entity, verb, *prop.values())
            print(res)
            results.append(res)
        except Exception as err:
            print('!!!', prop, '\n', err)

    return results


def src_props(qry, host=None, user=None, password=None):
    if host is None:
        host = src_defaults[0]

    if user is None:
        user = src_defaults[1]

    if password is None:
        password = src_defaults[2]

    return query_props(host, user, password, qry)


def dst_props(qry, host=None, user=None, password=None):
    if host is None:
        host = dst_defaults[0]

    if user is None:
        user = dst_defaults[1]

    if password is None:
        password = dst_defaults[2]

    return query_props(host, user, password, qry)
