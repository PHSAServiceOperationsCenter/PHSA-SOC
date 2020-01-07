"""
.. _exceptions:

:module:    mail_collector.exceptions

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

:updated:    May 29, 2019

Custom :exc:`Exception` classes for the :ref:`Mail Collector Application`

"""


class BadEventDataError(Exception):
    """
    Raised when the event data collected from the
    :ref:`Mail Borg Client Application` cannot be processed
    """


class BadHostDataFromEventError(Exception):
    """
    Raised when the host information contained in an event cannot be
    saved to :class:`citrus_borg.models.WinlogbeatHost`
    """


class SaveExchangeEventError(Exception):
    """
    Raised when one cannot save event data with no message information
    """


class SaveExchangeMailEventError(Exception):
    """
    Raised when one cannot save event data with message information
    """
