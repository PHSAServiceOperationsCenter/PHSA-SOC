"""
.. _config:

:module:    mail_borg.config

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

Configuration module for the :ref:`Mail Borg Client Application`

.. todo::

    there are some constants that need to move into the local configuration
"""
import collections
import configparser
import json
import socket
from json import JSONDecodeError

import pytimeparse

from requests import Session, urllib3, ConnectTimeout, ConnectionError

HTTP_PROTO = 'http'
"""
:class:`str` HTTP_PROTO determines if we use http or https to connect to the
configuration server

"""
VERIFY_SSL = False
"""
:class:`bool` VERIFY_SSL: check the validity of the SSL certificate when
using https
"""

SESSION = Session()
"""
:class:`requests.Session` SESSION: cached Session object to be reused by all
http connections
"""

SESSION.headers = {'Content-Type': 'application/json'}
if not SESSION.verify:
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

LOCAL_CONFIG = 'mail_borg.json'
"""
:class:`str` LOCAL_CONFIG is the name of the file used to cache the
configuration downloaded from the ``SOC Automation server``. This is the
configuration that will be used if loading the configuration from the server
is disabled
"""

WIN_EVT_CFG = dict(
    app_name='BorgExchangeMonitor',
    log_type='Application',
    evt_log_key='\\SYSTEM\\CurentControlSet\\Service\\EventLog',
    msg_dll=None)
"""
:class:`dict` WIN_EVENT_CFG contains the settings required for writing to the
Windows event log

:key app_name: the value of the application property in the event log

:key log_type: which windows log will be used for writing the events

:key evt_log_key: Windows registry key for the events log

:key msg_dll:

    Windows resources for providing descriptions when writing log events.
    If ``None``, the default DLL will be used

"""

INI_DEFAULTS = dict(use_cfg_srv=True,
                    cfg_srv_ip='10.2.50.38',
                    cfg_srv_port=8080,
                    cfg_srv_conn_timeout=30,
                    cfg_srv_read_timeout=120)
"""
:class:`dict` INI_DEFAULTS are the local configuration values that will be
used to overwrite the ``mail_borg.ini`` configuration file when the user
clicks on the ``Reset local config`` button
"""


def parse_duration(duration, to_minutes=False):
    """
    cast a duration  to an integer value representing seconds or minutes

    this function is needed because the main configuration as defined on
    the ``SOC Automation server`` is using JSON serialized
    :class:`django.db.models.DurationField` objects while the
    :ref:`Mail Borg Client Application` uses :class:`int` values for
    minutes and/or seconds

    :arg duration: the duration to be cast to :class:`int`

    :arg bool to_minutes:

        by default the cast is calculated to seconds. when this argument is
        ``True``, the cast is calculated to minutes
    """
    duration = pytimeparse.parse(duration)
    if to_minutes:
        duration = duration / 60

    return int(duration)


def load_base_configuration(current_base_configuration=None,
                            config_file='mail_borg.ini', section='SITE'):
    """
    Load (or reload) the basic configuration required for bootstrapping
    the :ref:`Mail Borg Client Application`

    There are three potential sources for the basic configuration:

    * a configuration file using the INI format

    * the :attr:`INI_DEFAULTS` defined in this module

    * the basic configuration fields from the :mod:`mail_borg.mail_borg_gui`
      module

    :arg dict current_base_configuration:

        If present, it represents the contents of the basic config fields
        from the main window of the :mod:`mail_borg.mail_borg_gui` module.
        if this argument is present, the function will return it.

        This argument is used under scenarios where the user has changed the
        initial basic configuration (e.g. the address of the configuration
        server), and now desires the preserve the new configuration

    :arg str config_file:

        The name of the INI file containing the basic configuration

        Default is 'mail_borg.ini'. If the INI file cannot be loaded,
        the values from :attr:`INI_DEFAULTS` will be returned

    :arg str section:

        The INI file section containing the basic configuration

        Default value is 'SITE'

    :returns: :class:`dict` with the basic configuration
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
    reload the basic configuration from the :attr:`INI_DEFAULTS`

    :note:

        it is possible that the values in the :attr:`INI_DEFAULTS` are out of
        date

    :returns: :class:`dict` with the default basic configuration
    """
    base_config = dict(INI_DEFAULTS)

    save_base_configuration(base_config)

    return base_config


def save_base_configuration(dict_config, config_file='mail_borg.ini'):
    """
    save the local configuration to an INI file

    :arg dict dict_config: the configuration to save

    :arg str config_file:

        The name of the INI file containing the basic configuration.
        Default is 'mail_borg.ini'.

    """
    config_parser = configparser.ConfigParser(
        allow_no_value=True, empty_lines_in_values=False)
    config_parser.read_dict(
        collections.OrderedDict(
            [('SITE', dict_config)]), source='<collections.OrderedDict>')

    with open(config_file, 'w') as file_handle:
        config_parser.write(file_handle, space_around_delimiters=True)


def load_config():
    """
    load the main configuration for the :ref:`Mail Borg Client Application`

    See :ref:`borg_remote_config` for more details about the structure of the
    main configuration.

    If the value of the ``use_cfg_srv`` key in the basic configuration is
    ``True``, the main configuration is loaded from the ``SOC Automation
    server`` via a REST over HTTP(S) call.
    Otherwise, the main configuration is loaded from the
    ``mail_borg.json`` JSON file. This file must be present in the
    same directory. Normally, this file is created the first time the
    :ref:`Mail Borg Client Application` is requesting a remote configuration.
    It is possible (but not recommended) to use a hand-crafted version of this
    file.

    When the main configuration is successfully loaded from the server, this
    function will cache the configuration to the ``mail_borg.json`` file.

    This function is also responsible for invoking the :func:`parse_duration`
    function in order to de-serialize duration fields to minutes or seconds
    expressed as :class:`int`.

    :returns:

        a complex structure that results from reading the JSON encoded string
        described in :ref:`borg_client_config` into Python

    :raises:

        generic :exc:`Exception` errors that are caught and used to update
        status fields in the main window of the :mod:`mail_borg.mail_borg_gui`
        module
    """
    config = dict()

    base_config = load_base_configuration()
    if not base_config.get('use_cfg_srv'):
        try:
            with open(LOCAL_CONFIG, 'r') as local_config:
                config = json.load(local_config)
            config['load_status'] = 'Using cached configuration.'
        except (JSONDecodeError, FileNotFoundError) as file_err:
            config['load_status'] = \
                f'Cannot load local configuration. Local error: {file_err}'
        # TODO if local load fails should we attempt to get config from server?
        return config

    try:
        config = get_config_from_server(base_config)
    except (ConnectTimeout, ConnectionError, ValueError) as server_err:
        config['load_status'] = f'Could not load config from server, ' \
                                f'{server_err}. '
    else:
        config['load_status'] = (
            'Loaded configuration %s from server'
            % config['exchange_client_config']['config_name'])

        # the first time the bot starts, it is possible that the
        # automation server is not aware of this bot. in that case a
        # default configuration is downloaded with a bogus host name
        # and then the real host name is injected into the configuration
        if config['host_name'] == 'host.not.exist':
            config['host_name'] = socket.gethostname()

        if not config['site']:
            config['site'] = {'site': 'site.not.exist'}

        with open(LOCAL_CONFIG, 'w') as local_config:
            json.dump(config, local_config, indent=4)

    return config


# TODO base_configuration could probably be passed as keyword args
#      or four (?) arguments to prevent the whole accessing it as a dict
def get_config_from_server(base_configuration):
    """
    Get the configuration from the ``SOC Automation server``

    This function is a wrapper around the GET request for the remote
    configuration.

    :arg dict base_configuration:

        the basic configuration values required for connecting to the server

    :returns: a JSON encoded :class:`str`

    :raises: lowest on this totem->requests.exceptions.ConnectTimeout, urllib3.exceptions.MaxRetryError, urllib3.exceptions.ConnectTimeoutError
             requests.exceptions.ConnectionError
             requests.exceptions.HTTPError
    """
    rest_endpoint = 'mail_collector/api/get_config'
    SESSION.verify = VERIFY_SSL
    cfg_ip = base_configuration.get('cfg_srv_ip')
    cfg_port = base_configuration.get('cfg_srv_port')
    hostname = socket.gethostname()

    url = f'{HTTP_PROTO}://{cfg_ip}:{cfg_port}/{rest_endpoint}/{hostname}/'

    response = SESSION.get(
        url,
        timeout=(base_configuration.get('cfg_srv_conn_timeout'),
                 base_configuration.get('cfg_srv_read_timeout')))

    if response.json():  # if there is json data in the response
        return response.json()[0]

    raise ValueError()

    return None
