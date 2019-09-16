"""
.. _mail_borg:

exchange monitoring client for borg bots

:module:    mail_borg

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    jul. 26, 2019

exchange monitoring client for borg bots
========================================

portability
-----------

because the logging mechanism is based on
`pywin32 <https://github.com/mhammond/pywin32>`_ this package is windows
only.

this design decision is due to the fact that we want to reuse the citrix
bots to run the exchange monitor programs and these bots already make use
of the windows events log to pass inforamtion to the PSOC automation
server.

log collection
--------------

the logger dependency on windows can be removed if we rewrite the logger
module to use ``logging.handlers.NTEventLogHandler`` and load the
NT handler conditionally based on the platform (replacing with a
``logging.handlers.SteamingFileHandler`` or a ``logging.handlers.Syslog``
handler. this will also require that an elastic search beat other than
winlogbeat is configured on the bot

"""
import sys

__version__ = '0.2.2-dev'