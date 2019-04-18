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
    'wait_receive': 60,
}
"""
:var dict DEFAULT: the default configuration

    don't change the password entry, it will be over written anyway and
    it will just create a security risk by placing password in github

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
    default['password'] = _get_password()
    return default


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
