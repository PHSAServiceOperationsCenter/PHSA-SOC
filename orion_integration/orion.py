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
from datetime import datetime

from django.conf import settings
from requests import Session, urllib3


SESSION = Session()
"""
:var SESSION: cached Session object to be reused by all Orion queries

    this way we will take advantage of http connection pooling

:vartype SESSION: `<request.Session.`
"""

SESSION.auth = (settings.ORION_USER, settings.ORION_PASSWORD)
SESSION.verify = settings.ORION_VERIFY_SSL_CERT
SESSION.headers = {'Content-Type': 'application/json'}

if not SESSION.verify:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


def serialize_custom_json(obj):
    """
    datetime objects need to be in ISO format before the json module can
    serialize
    """
    _ = None
    if isinstance(obj, datetime):
        _ = obj.isoformat()

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

        :returns: a dict ?

        :raises: a exception
        """
        response = SESSION.post(
            '{}/Query'.format(settings.ORION_URL),
            data=json.dumps(
                dict(query=orion_query, params=params),
                default=serialize_custom_json),
            timeout=settings.ORION_TIMEOUT
        )

        response.raise_for_status()

        return response.json()['results']
