"""
.. _mail_borg:

:module:    mail_borg

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    jul. 26, 2019

Exchange Monitoring Client Package
==================================

This package implements the :ref:`Mail Borg Client Application`.

Portability
-----------

Because the logging mechanism is based on
`pywin32 <https://github.com/mhammond/pywin32>`_ this package is **Windows
only**.

This design decision is due to the fact that we want to reuse the remote
Citrix bots to run :ref:`Mail Borg Client Application` instances as well.
Citrix diagnostics information collected by these bots is making use of
the Windows events log and a mechanism for disseminating such events to the
``SOC Automation server`` is already in place and running.

The :ref:`Mail Borg Client Application` is using a GUI interface and this will
also introduce various portability and/or deployment issues.

The :ref:`Mail Borg Config` module is fully portable.

The :ref:`Mail Borg Logger` module is absolutely not portable as implemented.

The :ref:`Mail Borg Mailer` module is not portable but making it platform
independent would require very little effort.

Note that the event dissemination is also Windows only. Any portability
efforts will have to take that into consideration.
"""
import sys

__version__ = '1.1.1-release_candidate'
