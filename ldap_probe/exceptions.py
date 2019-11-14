"""
ldap_probe.exceptions
---------------------

This module contains `custom exceptions
<https://docs.python.org/3.6/tutorial/errors.html#user-defined-exceptions>`__
used by the modules of the :ref:`Domain Controllers Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Nov. 12, 2019

"""


class ADProbeControllerError(Exception):
    """
    Custom :exc:`exceptions.Exception` class raised when one creates an
    instance of the :class:`ldap_probe.ad_probe.ADProbe` class without
    providing a domain controller object

    This is a fatal error as far as an AD probe operation is concerned.
    """
