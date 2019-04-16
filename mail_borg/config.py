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

USE_CACHED_CONFIG = True

DEFAULT = {

    'domain': 'PHSABC',
    'username': 'serban.teodorescu',
    'password': '',
    'send_to': ['serban.teodorescu@phsa.ca', ],
    'app_name': 'BorgExchangeMonitor',
    'log_type': 'Application',
    'evt_log_key': '\\SYSTEM\\CurentControlSet\\Service\\EventLog',
    'msg_dll': None,
}


def get_config():
    if USE_SERVER_SIDE:
        raise NotImplementedError('loading configuration from the server has'
                                  ' not yet been implemented')

    return DEFAULT
