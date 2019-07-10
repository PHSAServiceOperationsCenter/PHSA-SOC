"""
.. _lib:

various utility functions for the mail_collector app

:module:    mail_collector.queries

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Jun. 11, 2019

"""
from django.conf import settings


def event_sort_code(event_type):
    """
    map an event_type to a sort value

    :param str event_type:
    """
    mapper = settings.EVENT_TYPE_SORT
    if event_type in mapper:
        return mapper.get(event_type)
    return mapper.get('unknown')
