"""
.. _config:

configuration module for exchange monitoring borg bots

:module:    mail_borg.config

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    may 14, 2019

"""
import collections
import configparser
import json
import socket

import pytimeparse

from requests import Session, urllib3

HTTP_PROTO = 'http'
VERIFY_SSL = False
SESSION = Session()
"""
:var SESSION: cached Session object to be reused by all Orion queries

    this way we will take advantage of http connection pooling

:vartype SESSION: `<request.Session.`
"""

SESSION.headers = {'Content-Type': 'application/json'}
if not SESSION.verify:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOCAL_CONFIG = 'mail_borg.json'

WIN_EVT_CFG = dict(
    app_name='BorgExchangeMonitor',
    log_type='Application',
    evt_log_key='\\SYSTEM\\CurentControlSet\\Service\\EventLog',
    msg_dll=None)
"""
:var: WIN_EVENT_CFG:

    contains the settings required for writing to the Windows event log

:vartype: ``dict``
"""

INI_DEFAULTS = dict(use_cfg_srv=True,
                    cfg_srv_ip='10.2.50.38',
                    cfg_srv_port=8080,
                    cfg_srv_conn_timeout=30,
                    cfg_srv_read_timeout=120)


"""
use timedelta(seconds=pytimeparse.parse()).seconds() and seconds()/60 to
deserialize the durations

"""


def parse_duration(duration, to_minutes=False):
    """
    take a json serialized duration coming
    """
    duration = pytimeparse.parse(duration)
    if to_minutes:
        duration = duration / 60

    return int(duration)


def load_base_configuration(current_base_configuration=None,
                            config_file='mail_borg.ini', section='SITE'):
    """
    there are some settings that cannot live on the automation server,
    namely the ones telling the client how to connect to the server.

    we keep them in an ini file in the same directory as the application
    and if the ini file is not present, we fall back to the defaults in
    :var:`<INI_DEFAULTS>`

    :returns: ``dict`` with the basic configuration
    """
    if current_base_configuration:
        return dict(current_base_configuration)

    base_configuration = dict()

    config_parser = configparser.ConfigParser(
        allow_no_value=True, empty_lines_in_values=False)
    loaded = config_parser.read(config_file)

    if not loaded:
        base_configuration = dict(INI_DEFAULTS)
        return base_configuration

    base_configuration['use_cfg_srv'] = config_parser.getboolean(
        section, 'use_cfg_srv')
    base_configuration['cfg_srv_ip'] = config_parser.get(section, 'cfg_srv_ip')
    base_configuration['cfg_srv_port'] = config_parser.getint(
        section, 'cfg_srv_port')
    base_configuration['cfg_srv_conn_timeout'] = config_parser.getint(
        section, 'cfg_srv_conn_timeout')
    base_configuration['cfg_srv_read_timeout'] = config_parser.getint(
        section, 'cfg_srv_read_timeout')

    return base_configuration


def reset_base_configuration():
    """
    reset the local configuration to default
    """
    base_config = dict(INI_DEFAULTS)

    save_base_configuration(base_config)

    return base_config


def save_base_configuration(dict_config, config_file='mail_borg.ini'):
    """
    save the local configuration
    """
    config_parser = configparser.ConfigParser(
        allow_no_value=True, empty_lines_in_values=False)
    config_parser.read_dict(
        collections.OrderedDict(
            [('SITE', dict_config)]), source='<collections.OrderedDict>')

    with open(config_file, 'w') as file_handle:
        config_parser.write(file_handle, space_around_delimiters=True)


def load_config(current_base_config=None):
    """
    return the ``dict`` with the current configuration
    """
    config = dict()
    from_server = False

    base_config = load_base_configuration(current_base_config)

    if not base_config.get('use_cfg_srv'):
        try:
            config = get_config_from_file()
            config['load_status'] = (
                'Using cached configuration.')
        except Exception as file_err:  # pylint: disable=broad-except
            config['load_status'] = (
                'Cannot load local configuration.'
                'Local error: %s' % str(file_err))

    try:
        config = get_config_from_server(base_config)
    except Exception as err:  # pylint: disable=broad-except
        config = None

    if config:
        from_server = True
        config['load_status'] = (
            'Loaded configuration %s from server'
            % config['exchange_client_config']['config_name'])
        config['exchange_client_config']['mail_check_period'] = \
            parse_duration(
            config['exchange_client_config']['mail_check_period'],
            to_minutes=True)
        config['exchange_client_config']['check_mx_timeout'] = \
            parse_duration(
            config['exchange_client_config']['check_mx_timeout'])
        config['exchange_client_config']['min_wait_receive'] = \
            parse_duration(
            config['exchange_client_config']['min_wait_receive'])
        config['exchange_client_config']['max_wait_receive'] = \
            parse_duration(
            config['exchange_client_config']['max_wait_receive'])

    else:
        try:
            config = get_config_from_file()
            config['load_status'] = (
                'Loaded cached configuration. Server error: %s' % str(err))
        except Exception as file_err:
            config['load_status'] = (
                'Cannot load a configuration.'
                ' Server error: %s. Local error: %s' % (str(err),
                                                        str(file_err)))

    if from_server:
        dump_config_to_file(config)

    return config


def get_config_from_server(base_configuration):
    """
    get the configuration from server
    """
    rest_endpoint = 'mail_collector/api/get_config'
    SESSION.verify = VERIFY_SSL

    response = SESSION.get(
        '{}://{}:{}/{}/{}/'.format(
            HTTP_PROTO, base_configuration.get('cfg_srv_ip'),
            base_configuration.get('cfg_srv_port'), rest_endpoint,
            socket.gethostname()),
        timeout=(base_configuration.get('cfg_srv_conn_timeout'),
                 base_configuration.get('cfg_srv_read_timeout')))

    response.raise_for_status()

    return response.json()[0]


def get_config_from_file(json_file=LOCAL_CONFIG):
    """
    get the comfiguration from a local file
    """
    try:
        with open(json_file, 'r') as local_config:
            config = json.load(local_config)

        local_config.close()
    except Exception as err:
        raise err

    return config


def dump_config_to_file(config, json_file=LOCAL_CONFIG):
    """
    dump the latest config from servetr to the local file. we need it in
    case the server becomes unavailable
    """
    try:
        with open(json_file, 'w') as local_config:
            json.dump(config, local_config, indent=4)

        local_config.close()
    except Exception as err:
        raise err
