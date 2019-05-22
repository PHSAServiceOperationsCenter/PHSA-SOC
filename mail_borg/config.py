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


PASSWD = 'passwd'
EMAILS = 'emails.txt'

NOT_A_PASSWORD = 'not a password'

DEFAULTS = dict(autorun=False,
                use_server_config=False,
                debug=False,
                domain='PHSABC',
                username='svc_SOCmailbox',
                autodiscover=True,
                exchange_server=None,
                password_file=PASSWD,
                email_addresses_file=EMAILS,
                witness_addresses='',
                email_subject='exchange monitoring message',
                app_name='BorgExchangeMonitor',
                log_type='Application',
                evt_log_key='\\SYSTEM\\CurentControlSet\\Service\\EventLog',
                msg_dll=None,
                mail_every_minutes=20,
                force_ascii_email=True,
                allow_utf8_email=False,
                check_email_mx=True,
                check_mx_timeout=5,
                min_wait_receive=3,
                step_wait_receive=3,
                max_wait_receive=120,
                site='noname',
                tags='[default config]')


def load_config(config_file='mail_borg.ini', section='SITE'):
    """
    return the ``dict`` with the current configuration
    """
    config = dict()

    config_parser = configparser.ConfigParser(
        allow_no_value=True, empty_lines_in_values=False)
    loaded = config_parser.read(config_file)

    if not loaded:
        config = dict(DEFAULTS)

        # password and email addresses come from files
        config['password'] = _get_password(
            password_file=config.get('password_file'))
        config.pop('password_file')

        config['email_addresses'] = _get_emails(
            config.get('email_addresses_file'))
        config.pop('email_addresses_file')

        if config['use_server_config']:
            return get_config_from_server()

        return config

    config['use_server_config'] = config_parser.getboolean(section,
                                                           'use_server_config')

    if config['use_server_config']:
        return get_config_from_server()

    config['debug'] = config_parser.getboolean(section, 'debug')
    config['autorun'] = config_parser.getboolean(section, 'autorun')
    config['domain'] = config_parser.get(section, 'domain')
    config['username'] = config_parser.get(section, 'username')

    config['autodiscover'] = config_parser.getboolean(section, 'autodiscover')
    config['exchange_server'] = config_parser.get(section, 'exchange_server')

    config['password'] = _get_password(
        password_file=config_parser.get(section, 'password_file'))

    config['email_addresses'] = _get_emails(config_parser.get(
        section, 'email_addresses_file'))
    config['witness_addresses'] = config_parser.get(
        section, 'witness_addresses')

    config['app_name'] = config_parser.get(section, 'app_name')
    config['log_type'] = config_parser.get(section, 'log_type')
    config['evt_log_key'] = config_parser.get(section, 'evt_log_key')

    config['msg_dll'] = config_parser.get(section, 'msg_dll')

    config['mail_every_minutes'] = config_parser.getint(
        section, 'mail_every_minutes')
    config['force_ascii_email'] = config_parser.getboolean(
        section, 'force_ascii_email')
    config['allow_utf8_email'] = config_parser.getboolean(
        section, 'allow_utf8_email')
    config['check_email_mx'] = config_parser.getboolean(
        section, 'check_email_mx')
    config['check_mx_timeout'] = config_parser.getint(
        section, 'check_mx_timeout')
    config['min_wait_receive'] = config_parser.getint(
        section, 'min_wait_receive')
    config['step_wait_receive'] = config_parser.getint(
        section, 'step_wait_receive')
    config['max_wait_receive'] = config_parser.getint(
        section, 'max_wait_receive')

    config['site'] = config_parser.get(section, 'site')
    config['tags'] = config_parser.get(section, 'tags')

    config['email_subject'] = config_parser.get(section, 'email_subject')

    return config


def save_config(dict_config, config_file='mail_borg.ini'):
    """
    save configuration file
    """

    # password is a special case, we must save the password to a file,
    # pop the password from the configuration dictionary (otherwise it will
    # be saved in clear in a file thatmay end up in github),
    # and save the file name to the configuration
    dict_config['password_file'] = _set_passwd(dict_config.get('password'))
    dict_config.pop('password')

    dict_config['email_addresses_file'] = _set_emails(
        dict_config.get('email_addresses'))
    dict_config.pop('email_addresses')

    config_parser = configparser.ConfigParser(
        allow_no_value=True, empty_lines_in_values=False)
    config_parser.read_dict(
        collections.OrderedDict(
            [('SITE', dict_config)]), source='<collections.OrderedDict>')
    with open(config_file, 'w') as file_handle:
        config_parser.write(file_handle, space_around_delimiters=True)


def load_default_config():
    """
    load the default configuration
    """
    return load_config(config_file='default_mail_borg.ini', section='DEFAULT')


def get_config_from_server():
    """
    return the configuration from the server
    """
    raise NotImplementedError('loading configuration from the server has'
                              ' not yet been implemented')


def _get_password(password_file=PASSWD):
    """
    absolutely not a safe way to deal with passwords but at least with
    this we can keep the damned passwords from showing in the github history

    mea culpa, mea culpa, mea maxima culpa
    """
    try:
        with open(password_file, 'r') as fhandle:
            passwd = fhandle.readline()
    except FileNotFoundError:
        _set_passwd(NOT_A_PASSWORD)
        return NOT_A_PASSWORD

    return passwd


def _get_emails(emails_file=EMAILS):
    try:
        with open(emails_file, 'r') as file_handle:
            emails = file_handle.read().replace('\n', ',')
        return emails
    except FileNotFoundError:
        return ''


def _set_passwd(password, password_file=PASSWD):
    with open(password_file, 'w') as file_handle:
        file_handle.write(password)

    return password_file


def _set_emails(emails, emails_file=EMAILS):
    with open(emails_file, 'w') as file_handle:
        file_handle.write(emails.replace(',', '\n'))

    return emails_file
