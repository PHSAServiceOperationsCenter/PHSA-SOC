"""
.. _exceptions:

custom ``Exception`` classes for the mail_collector application

:module:    mail_collector.exceptions

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    May 29, 2019

"""


class BadEventDataError(Exception):
    """
    raise when the event data collected from the Exchange Monitoring Client
    application cannot be processed
    """


class BadHostDataFromEventError(Exception):
    """
    raise when the host information contained in an event cannot be
    saved to :class:`<citrus_borg.models.WinlogbeatHost>`
    """


class SaveExchangeEventError(Exception):
    """
    raise when one cannot save event data with no message information
    """


class SaveExchangeMailEventError(Exception):
    """
    raise when one cannot save event data with message information
    """
