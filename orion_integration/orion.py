"""
orion_integration.orion
-----------------------

This module provides the `HTTP(S)` client for the `Orion REST API`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
import json
import decimal

from datetime import datetime, timedelta

from requests import Session, urllib3

from citrus_borg.dynamic_preferences_registry import get_preference

SESSION = Session()
"""
cached :class:`requests.Session` object that allows the client to take advantage
of `HTTP persistent connections
<https://en.wikipedia.org/wiki/HTTP_persistent_connection>`__
"""

SESSION.headers = {'Content-Type': 'application/json'}

if not SESSION.verify:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def serialize_custom_json(obj):
    """
    custom `JSON encoder
    <https://docs.python.org/3.6/library/json.html?highlight=json#json.JSONEncoder>`__
    for :class:`datetime.datetime` objects; see `default(o)
    <https://docs.python.org/3.6/library/json.html?highlight=json#json.JSONEncoder.default>`__

    The `json module
    <https://docs.python.org/3.6/library/json.html?highlight=json#module-json>`__
    cannot serialize :class:`datetime.datetime` objects directly because `JSON
    <https://www.json.org/>`__ doesn't have a suitable data type. This function
    converts :class:`datetime.datetime` objects to `ISO 8601
    <https://en.wikipedia.org/wiki/ISO_8601>`__ strings which can then be encoded
    by the `json module
    <https://docs.python.org/3.6/library/json.html?highlight=json#module-json>`__.
    """
    _ = None
    if isinstance(obj, datetime):
        _ = obj.isoformat()

    if isinstance(obj, decimal.Decimal):
        _ = str(obj)

    if isinstance(obj, timedelta):
        return {'days': obj.days,
                'seconds': obj.seconds,
                'microseconds': obj.microseconds}

    return _

# pylint:disable=R0903


class OrionClient:
    """
    `REST <https://en.wikipedia.org/wiki/Representational_state_transfer>`__
    client class for the `Orion SDK
    <https://github.com/solarwinds/orionsdk-python#orion-sdk-for-python>`__
    """

    @classmethod
    def query(cls, orion_query, **params):
        """
        query the `Orion` server

        :arg str query: the query string
        :arg dict params: the query params

        :returns: the data that matches the query
        :rtype: dict

        """

        # need to configure the SESSION object here because the
        # user configurable settings will not work if used at the
        # module level
        SESSION.auth = (get_preference('orionserverconn__orion_user'),
                        get_preference('orionserverconn__orion_password'))
        SESSION.verify = get_preference(
            'orionserverconn__orion_verify_ssl_cert')

        response = SESSION.post(
            '{}/Query'.format(
                get_preference('orionserverconn__orion_rest_url')),
            data=json.dumps(
                dict(query=orion_query, parameters=params),
                default=serialize_custom_json),
            timeout=(get_preference('orionserverconn__orion_conn_timeout'),
                     get_preference('orionserverconn__orion_read_timeout'))
        )

        response.raise_for_status()

        return response.json()['results']
