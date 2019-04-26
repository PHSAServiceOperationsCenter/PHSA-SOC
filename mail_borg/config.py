"""
.. _config:

configuration module for exchange monitoring borg bots

:module:    mail_borg.config

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    apr. 12, 2019

"""
import socket

DEBUG = True

USE_SERVER_SIDE = False
"""
:var bool USER_SERVER_SIDE:

    load the configuration values from the PHSA automation server?
"""

DEFAULT = {
    'domain': 'PHSABC',
    'username': 'serban.teodorescu',
    'password': None,
    'email_addresses': ['serban.teodorescu@phsa.ca', ],
    'email_subject': 'exchange monitoring message',
    'app_name': 'BorgExchangeMonitor',
    'log_type': 'Application',
    'evt_log_key': '\\SYSTEM\\CurentControlSet\\Service\\EventLog',
    'msg_dll': None,
    'check_mx_timeout': 5,
    'min_wait_receive': 3,
    'step_wait_receive': 3,
    'max_wait_receive': 120,
    'witness_addresses': ['james.reilly@phsa.ca', ],
    'site': 'willingdon',
}
"""
:var dict DEFAULT: the default configuration

    don't change the password entry, it will be over written anyway and
    it will just create a security risk by placing a domain account
    password in github

    msg_dll is the file containing the messages required by the windows
    events log. if set to ``None``, the default provided by the pywin32
    python package is provided
"""


def get_config():
    """
    return the ``dict`` with the current configuration
    """
    if USE_SERVER_SIDE:
        return get_config_from_server()

    default = dict(DEFAULT)
    default['email_subject'] = set_subject(default.get('email_subject'),
                                           default.get('site'))
    default['password'] = _get_password()
    return default


def set_subject(subject, site=None):
    """
    tag the subject line with the fqdn, site information if available,
    and debug information

    this is mostly useful when cc'ing human email addresses for manual
    monitoring. the tags will make it easy to create exchange rules for the
    monitoring messages
    """
    tags = '[DEBUG]' if DEBUG else None
    tags += '[{}]'.format(socket.getfqdn())

    subject = '{}{}'.format(tags, subject)

    if site:
        return '{} originating from {}'.format(subject, site)

    return subject


def get_config_from_server():
    """
    return the configuration from the server
    """
    raise NotImplementedError('loading configuration from the server has'
                              ' not yet been implemented')


def _get_password(password_file='passwd'):
    """
    absolutely not a safe way to deal with passwords but at least with
    this we can keep the damned passwords from showing in the github history

    mea culpa, mea culpa, mea maxima culpa
    """
    with open(password_file, 'r') as fhandle:
        passwd = fhandle.readline()

    return passwd
