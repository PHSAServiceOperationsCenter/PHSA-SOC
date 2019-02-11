"""
.. _orion:

orion classes for the orion_integration app

:module:    p_soc_auto.orion_integration.orion

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Aug. 8, 2018

"""
import json
import decimal

from datetime import datetime, timedelta

from requests import Session, urllib3

from citrus_borg.dynamic_preferences_registry import get_preference

SESSION = Session()
"""
:var SESSION: cached Session object to be reused by all Orion queries

    this way we will take advantage of http connection pooling

:vartype SESSION: `<request.Session.`
"""

SESSION.auth = (get_preference('orionserverconn__orion_user'),
                get_preference('orionserverconn__orion_password'))
SESSION.verify = get_preference('orionserverconn__orion_verify_ssl_cert')
SESSION.headers = {'Content-Type': 'application/json'}

if not SESSION.verify:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def serialize_custom_json(obj):
    """
    datetime objects need to be in ISO format before the json module can
    serialize them
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


class OrionClient():
    """
    :class OrionClient: a class that acts as a REST client for the Orion SDK
    """

    @classmethod
    def query(cls, orion_query, **params):
        """
        query the Orion server

        :arg str query: the query string
        :arg dict params: the query params

        :returns: a `dict`

        :raises:
        """
        response = SESSION.post(
            '{}/Query'.format(
                get_preference('orionserverconn__orion_rest_url')),
            data=json.dumps(
                dict(query=orion_query, params=params),
                default=serialize_custom_json),
            timeout=(get_preference('orionserverconn__orion_conn_timeout'),
                     get_preference('orionserverconn__orion_read_timeout'))
        )

        response.raise_for_status()

        return response.json()['results']
