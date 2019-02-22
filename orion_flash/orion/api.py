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
import logging
import requests

from requests import urllib3
from requests.adapters import HTTPAdapter
from requests.packages.urllib3.util.retry import Retry  # @UnresolvedImport

from orionsdk import SwisClient

from django.conf import settings

import qv

from citrus_borg.dynamic_preferences_registry import get_preference

LOG = logging.getLogger('orion_flash')


SRC_DEFAULTS = (settings.ORION_HOSTNAME,
                settings.ORION_USER, settings.ORION_PASSWORD)
DST_DEFAULTS = ('10.248.211.70',
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

        super().__init__(*args, verify, logger)

    def copy_custom_props(self, src_props=None):
        """
        copy custom properties between servers

        :arg src: the source orion server
        """
        results = []

        if src_props is None:
            src_props = SourceSwis().query(query=qv.CUSTOM_PROPS_QUERY)

        for prop in src_props:
            self.logger.info(
                'copying custom property Table: %s, Field: %s',
                prop.get('Table'), prop.get('Field'))
            if self.query(query=qv.CUSTOM_PROPS_QUERY,
                          Table=prop.get('Table'), Field=prop.get('Field')):

                self.logger.debug(
                    'custom property Table: %s, Field: %s exists, skipping',
                    prop.get('Table'), prop.get('Field'))
                continue

            results.append(
                self._invoke(
                    target=prop.get('TargetEntity'), verb=qv.CUSTOM_PROPS_VERB,
                    data=[prop.get(key, None) for key
                          in qv.CUSTOM_PROPS_INVOKE_ARGS]))

        return results

    def _invoke(self, target, verb, data):
        try:
            return self.orion_connection.invoke(target, verb, *data)
        except Exception:  # pylint: disable=broad-except
            self.logger.exception(
                'cannot create custom property: %s against target entity: %s',
                data[0], target)
