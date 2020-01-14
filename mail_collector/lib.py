"""
.. _lib:

various utility functions for the mail_collector app

:module:    mail_collector.queries

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

:updated:    Jun. 11, 2019

"""
from django.conf import settings


def event_sort_code(event_type):
    """
    provide custom sorting for sorting instances of
    :class:`mail_collector.models.MailBotLogEvent`
    instances by event type

    the proper order is ['connect', 'send', 'receive'] which is not
    alphabetical

    :param str event_type: the event type provided by the windows event data

    :return: the custom sort mapping for the event type
    :rtype: int
    """
    mapper = settings.EVENT_TYPE_SORT
    if event_type in mapper:
        return mapper.get(event_type)
    return mapper.get('unknown')
