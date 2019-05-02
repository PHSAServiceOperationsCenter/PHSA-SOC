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
import configparser
import socket

CONFIG = configparser.ConfigParser(
    allow_no_value=True, empty_lines_in_values=False)


def load_config(config_file='mail_borg.ini'):
    """
    return the ``dict`` with the current configuration
    """
    CONFIG.read(config_file)

    config = dict()
    config['use_server_config'] = CONFIG.getboolean('SITE',
                                                    'use_server_config')

    if config['use_server_config']:
        return get_config_from_server()

    config['debug'] = CONFIG.getboolean('SITE', 'debug')
    config['autorun'] = CONFIG.getboolean('SITE', 'autorun')
    config['domain'] = CONFIG.get('SITE', 'domain')
    config['username'] = CONFIG.get('SITE', 'username')

    config['password'] = _get_password(
        password_file=CONFIG.get('SITE', 'password_file'))

    config['email_addresses'] = CONFIG.get(
        'SITE', 'email_addresses').split(',')
    config['witness_addresses'] = CONFIG.get(
        'SITE', 'witness_addresses').split(',')
    config['email_subject'] = CONFIG.get('SITE', 'email_subject')

    config['app_name'] = CONFIG.get('SITE', 'app_name')
    config['log_type'] = CONFIG.get('SITE', 'log_type')
    config['evt_log_key'] = CONFIG.get('SITE', 'evt_log_key')

    config['msg_dll'] = CONFIG.get('SITE', 'msg_dll')

    config['mail_every_minutes'] = CONFIG.getint('SITE', 'mail_every_minutes')
    config['check_mx_timeout'] = CONFIG.getint('SITE', 'check_mx_timeout')
    config['min_wait_receive'] = CONFIG.getint('SITE', 'min_wait_receive')
    config['step_wait_receive'] = CONFIG.getint('SITE', 'step_wait_receive')
    config['max_wait_receive'] = CONFIG.getint('SITE', 'max_wait_receive')

    config['site'] = CONFIG.get('SITE', 'site')
    config['tags'] = CONFIG.get('SITE', 'tags')

    return config


def set_subject(subject, site=None, debug=False):
    """
    tag the subject line with the fqdn, site information if available,
    and debug information

    this is mostly useful when cc'ing human email addresses for manual
    monitoring. the tags will make it easy to create exchange rules for the
    monitoring messages
    """
    tags = '[DEBUG]' if debug else None
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
