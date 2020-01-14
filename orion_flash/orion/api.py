"""
.. _common:

functions and methods for the orion package

:module:    p_soc_auto.orion_flash.orion.common

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

:updated:    Feb. 21, 2019

"""
import logging
import requests

from requests import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # @UnresolvedImport

from orionsdk import SwisClient

from django.conf import settings

from .qv import (
    ALL_CUSTOM_PROPS_QUERY, FILTERED_CUSTOM_PROPS_QUERY,
    CUSTOM_PROPS_VALS_VERB,
    CUSTOM_PROPS_VALS_INVOKE_ARGS, VALUES_FOR_CUSTOM_PROP_QUERY,
    NODE_PROPS_QUERY, NODE_URI_QUERY, ALL_NODES_IPADDRESS_QUERY,
    NODE_CUSTOM_PROPS_QUERY,
)

from citrus_borg.dynamic_preferences_registry import get_preference


LOG = logging.getLogger('orion_flash')


SRC_DEFAULTS = (settings.ORION_HOSTNAME,
                settings.ORION_USER, settings.ORION_PASSWORD)
DST_DEFAULTS = (
    get_preference('orionserverconn__orion_hostname'),
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


class SourceSwis():  # pylint: disable=too-few-public-methods
    """
    wrap around the SwisClient for a cleaner look

    provides only methods for reading data from the server
    """

    def __init__(
            self, *args, verify=settings.ORION_VERIFY_SSL_CERT, logger=LOG):
        """
        :arg args: (host, user, password) for the orion server

        this is not the cleanest implementation because we are not doing
        any error checking. OTOH, this is not exactly aiming for
        production quality but for expediency

        """
        self.logger = logger
        if not args:
            args = SRC_DEFAULTS

        # pylint: disable=no-value-for-parameter
        self.orion_connection = SwisClient(*args, verify=verify)
        # pylint: enable=no-value-for-parameter

    def query(self, query, **params):
        """
        call the SwisClient query method and return just the results
        """
        return self.orion_connection.query(query, **params).get('results')


class DestSwis(SourceSwis):
    """
    another wrap around for :class:`<orionsdk.SwisClient>`

    this one will add write methods as well, probably delete methods if we
    need them
    """

    def __init__(
            self, *args,
            verify=get_preference('orionserverconn__orion_verify_ssl_cert'),
            logger=LOG):
        """
        override the parent constructor to prefer defaults specific to the
        target server
        """
        if not args:
            args = DST_DEFAULTS

        super().__init__(*args, verify=verify, logger=logger)

    def copy_custom_props(self, src_props=None):
        """
        copy custom properties between servers

        :arg src: the source orion server
        """
        results = []

        if src_props is None:
            src_props = SourceSwis().query(query=ALL_CUSTOM_PROPS_QUERY)

        for prop in src_props:
            self.logger.info(
                'copying custom property Table: %s, Field: %s',
                prop.get('Table'), prop.get('Field'))
            if self.query(query=FILTERED_CUSTOM_PROPS_QUERY,
                          table=prop.get('Table'), field=prop.get('Field')):
                self.logger.debug(
                    'custom property Table: %s, Field: %s exists, skipping',
                    prop.get('Table'), prop.get('Field'))
                continue

            values = SourceSwis().query(
                query=VALUES_FOR_CUSTOM_PROP_QUERY,
                table=prop.get('Table'), field=prop.get('Field'))
            if values:
                values = [value.get('Value') for value in values]
                self.logger.info('also copying values %s', values)

            prop['Values'] = values

            results.append(
                self._invoke(
                    target=prop.get('TargetEntity'),
                    verb=CUSTOM_PROPS_VALS_VERB,
                    data=[prop.get(key, None) for key
                          in CUSTOM_PROPS_VALS_INVOKE_ARGS]))

        return results

    def update_nodes_with_props(self, src=None):
        """
        update node properties
        """
        if src is None:
            src = SourceSwis()

        if not isinstance(src, SourceSwis):
            raise TypeError(
                'invalid type %s for %s object' % (type(src), src))

        for ipaddress in self.ipaddresses:

            src_props = src.query(
                query=NODE_PROPS_QUERY, ipaddress=ipaddress)
            if not src_props:
                self.logger.info('there is no source spoon for %s', ipaddress)
                continue

            src_props = src_props[0]
            uri = self._node_uri_by_ip(ipaddress)

            try:
                self.orion_connection.update(uri=uri, **src_props)
            except Exception:  # pylint: disable=broad-except
                self.logger.exception(
                    'cannot update node at %s with %s', uri, src_props)

            self.logger.info('updated %s with %s', uri, src_props)

    def update_nodes_with_custom_props(self, src=None):
        if src is None:
            src = SourceSwis()

        if not isinstance(src, SourceSwis):
            raise TypeError(
                'invalid type %s for %s object' % (type(src), src))

        for ipaddress in self.ipaddresses:

            src_props = src.query(
                query=NODE_CUSTOM_PROPS_QUERY, ipaddress=ipaddress)
            if not src_props:
                self.logger.info('there is no source spoon for %s', ipaddress)
                continue

            src_props = src_props[0]
            src_props.pop('NodeID', None)
            src_props.pop('IPAddress', None)
            uri = self._node_uri_by_ip(ipaddress)

            try:
                self.orion_connection.update(
                    uri='{}/CustomProperties'.format(uri), **src_props)
            except Exception:  # pylint: disable=broad-except
                self.logger.exception(
                    'cannot update node at %s with %s', uri, src_props)

            self.logger.info('updated %s with %s', uri, src_props)

    def _node_uri_by_ip(self, ipaddress):
        return self.query(query=NODE_URI_QUERY,
                          ipaddress=ipaddress)[0].get('Uri')

    @property
    def ipaddresses(self):
        ipaddresses = self.query(ALL_NODES_IPADDRESS_QUERY)
        if not ipaddresses:
            raise ValueError('there are no spoons on the destination server')

        return [ipaddress.get('IPAddress') for ipaddress in ipaddresses]

    def _invoke(self, target, verb, data):
        try:
            self.orion_connection.invoke(target, verb, *data)
            return 'executed %s against %s with data %s' % (verb, target, data)
        except Exception:  # pylint: disable=broad-except
            self.logger.exception(
                'cannot create custom property: %s against target entity: %s',
                data[0], target)
