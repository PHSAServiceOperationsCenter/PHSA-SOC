"""
.. _assimilation:

Functions for parsing `Windows` log events to `Python` structures
-----------------------------------------------------------------

:module:    citrus_borg.locutus.assimilation

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    nov. 128, 2018

"""
import collections
import json
import logging
import socket

from django.utils.dateparse import parse_duration, parse_datetime

from citrus_borg.dynamic_preferences_registry import get_preference


def _get_logger():
    """
    :returns: a private :class:`logging.Logger` to be used for other functions
        in this modulethat require a `logging` object and are not invoked with
        one provided by the caller
    """
    return logging.getLogger('citrus_borg')


def get_ip_for_host_name(host_name=None, ip_list=None):
    """
    :returns: the IP address that goes with a known host name if it can be
        resolved or `None` otherwise

    :arg str host_name: the host name as reported from external sources

    :arg list ip_list: a list of ip addresses for the host

    :raises:

        :exc:`ValueError` if the `host_naame` is missing

    This function loops through the items in the `ip_list` :class:`list` argument
    and returns the one that will resolve to the value of the `host_name` argument.
    The function uses :func:`socket.gethostbyaddr` to retrieve the resolved
    host for each item in the `ip_list` :class:`list`. If the resolved host matches
    the value of the `host_name`, the item in the `list` is the `IP` address
    that we are looking for.

    """
    def _gethostbyname():
        """
        this is the fall-back function for :func:`get_ip_for_host_name`

        Sometimes there are no entries in the :class:`ip-list <list>`. We will try
        to resolve the `host_name` argument using 
        and we will return that. Or we will return`None` if
        :func:`socket.gethostbyname` barfs.
        """
        try:
            return socket.gethostbyname(host_name)
        except:  # pylint: disable=W0702
            # or just give up like a little wimp
            return None

    if host_name is None:
        raise ValueError('host_name argument is mandatory')

    host_name = str(host_name)

    if ip_list is None:
        return _gethostbyname()

    if not isinstance(ip_list, (list, tuple)):
        return _gethostbyname()

    ip_address = None
    for _ip_address in ip_list:
        try:
            _host_name, _alias_list, _ip_list = \
                socket.gethostbyaddr(ip_address)
            if host_name in _host_name:
                ip_address = _ip_address
            continue
        except:  # pylint: disable=W0702
            continue

    if ip_address:
        return ip_address

    return _gethostbyname()


def process_borg(body=None, logger=None):
    """
    :returns; a :func:`colections.namedtuple` object

    The `Borg` `object` has the following properties: 'source_host',
    'record_number', 'opcode', 'level', 'event_source', 'windows_log',
    'borg_message', 'mail_borg_message'.

    The 'event-source' propety will determine which application will ingest the
    `Windows` `event`.
    """
    if logger is None:
        logger = _get_logger()

    if body is None:
        raise ValueError('body argument is mandatory')

    borg = collections.namedtuple(
        'Borg', [
            'source_host', 'record_number', 'opcode', 'level',
            'event_source', 'windows_log', 'borg_message', 'mail_borg_message'
        ]
    )

    borg.source_host = process_borg_host(body.get('host', None))
    borg.record_number = body.get('record_number', 0)
    borg.opcode = body.get('opcode', None)
    borg.level = body.get('level', None)
    borg.event_source = body.get('source_name', None)
    borg.windows_log = body.get('log_name', None)

    if borg.event_source in get_preference('citrusborgevents__source').split(','):
        borg.borg_message = process_borg_message(body.get('message', None))
        borg.mail_borg_message = None
    elif borg.event_source in get_preference('exchange__source').split(','):
        borg.borg_message = None
        borg.mail_borg_message = process_exchange_message(
            json.loads(body.get('event_data')['param1']), logger)

    return borg


def process_borg_host(host=None):
    """
    the input are the values for the name and ip keys in the host dictionary
    returned by the winlogbeat + logstash combination for a given windows
    event. Here is a sample:

    host: {
        'name': 'baby_d',
        'mac': ['02:00:4c:4f:4f:50', '9e:b6:d0:8a:23:df', 'ae:b6:d0:8a:23:df',
                '9c:b6:d0:8a:23:df', '9c:b6:d0:8a:23:e0', '02:15:03:a1:a2:5e'],
        'ip': ['fe80::449b:87fb:5758:b29', '169.254.11.41',
               'fe80::bc38:afcd:34ba:8de2', '169.254.141.226',
               'fe80::5181:28ba:b614:957a', '169.254.149.122',
               'fe80::441f:c81b:f69b:e22b', '10.42.27.105',
               'fe80::e947:1c6c:3ce9:ec12', '169.254.236.18',
               'fe80::dd4c:609f:d278:2d75', '172.24.70.33'],
        'id': 'e4ee2cbd-baa7-4e97-abfc-afd5a8e46730',
        'architecture': 'x86_64',
        'os': {
            'version': '10.0', 'build': '17134.407', 'platform': 'windows',
            'family': 'windows'
        }
    }

    :returns: a namedtuple with the host properties that we need
    """
    if host is None:
        raise ValueError('host argument is mandatory')

    borg_host = collections.namedtuple(
        'BorgHost', ['host_name', 'ip_address', ])

    borg_host.host_name = host.get('name', None)
    borg_host.ip_address = get_ip_for_host_name(host.get('name', None),
                                                host.get('ip', None))

    return borg_host


def process_borg_message(message=None, logger=None):
    """
    this is the string when success

    Successful logon: to resource: PMOffice - CST Brokered by device: \
        PHSACDCTX42

    Test Details:
    ----------------------
    Latest Test Result: True
    Storefront Connection Time: 00:00:03.1083110
    Receiver Startup: 00:00:01.1673405
    Connection Time: 00:00:00.4353095
    Logon Time: 00:00:04.0380058
    Logoff Time: 00:00:05.3581214


    and here's the bad honey

    Failed logon to resource: PMOffice - CST
    Failure reason: The Connection failed during session logon.
    Failure details:

    Test Output:
    ----------------------
    13:51:17 - Starting storefront connection
    13:51:17 - Initialising storefront
    13:51:17 - Requesting resources
    13:51:19 - Received resources
    13:51:19 - Resource found, requesting ICA file
    13:51:20 - Connecting to: 104.170.202.132:1494
    13:51:20 - ICA file received
    13:51:20 - Initialising received
    13:51:21 - Connecting received
    13:51:21 - Connect received
    13:51:22 - On disconnect
    13:51:22 - Total connection time: 0


    """
    if logger is None:
        logger = _get_logger()

    if message is None:
        raise ValueError('message argument is mandatory')

    borg_message = collections.namedtuple(
        'BorgMessage', [
            'state', 'broker', 'test_result', 'storefront_connection_duration',
            'receiver_startup_duration', 'connection_achieved_duration',
            'logon_achieved_duration', 'logoff_achieved_duration',
            'failure_reason', 'failure_details', 'raw_message'
        ]
    )

    borg_message.raw_message = str(message)
    message = message.split('\n')
    borg_message.state = message[0].split()[0]

    if borg_message.state.lower() in ['successful']:
        logger.debug('citrus borg event state: successful')
        borg_message.broker = message[0].split()[-1]
        borg_message.test_result = bool(message[4].split()[-1])
        borg_message.storefront_connection_duration = \
            parse_duration(message[5].split()[-1])
        borg_message.receiver_startup_duration = \
            parse_duration(message[6].split()[-1])
        borg_message.connection_achieved_duration = \
            parse_duration(message[7].split()[-1])
        borg_message.logon_achieved_duration = \
            parse_duration(message[8].split()[-1])
        borg_message.logoff_achieved_duration = \
            parse_duration(message[9].split()[-1])
        borg_message.failure_reason = None
        borg_message.failure_details = None

    elif borg_message.state.lower() in ['failed']:
        logger.debug('citrus borg event state: failed')
        borg_message.failure_reason = message[1].split(': ')[1]
        borg_message.failure_details = '\n'.join(message[-12:-1])
        borg_message.broker = None
        borg_message.test_result = False
        borg_message.storefront_connection_duration = None
        borg_message.receiver_startup_duration = None
        borg_message.connection_achieved_duration = None
        borg_message.logon_achieved_duration = None
        borg_message.logoff_achieved_duration = None
    else:
        logger.error('citrus borg event state undetermined %s',
                     borg_message.raw_message)
        borg_message.state = 'undetermined'
        borg_message.broker = None
        borg_message.test_result = False
        borg_message.storefront_connection_duration = None
        borg_message.receiver_startup_duration = None
        borg_message.connection_achieved_duration = None
        borg_message.logon_achieved_duration = None
        borg_message.logoff_achieved_duration = None
        borg_message.failure_reason = None
        borg_message.failure_details = None

    return borg_message


def process_exchange_message(message=None, logger=None):
    """
    process event data from ExchangeMonitorEvents

    dict_keys(['type', 'status', 'message', 'account',
               'from_email', 'to_emails', 'message_uuid', exception,
               'from_address', 'to_addresses', 'created', 'sent', 'received'])

    """
    if logger is None:
        logger = _get_logger()

    if message is None:
        raise TypeError('%s object is not a valid argument' % type(message))

    ExchangeEvent = collections.namedtuple(
        'ExchangeEvent',
        ['event_group_id', 'event_type', 'event_status', 'event_message',
         'event_exception', 'mail_account', 'event_body']
    )

    ExchangeMessage = collections.namedtuple(
        'ExchangeMessage',
        ['sent_from', 'sent_to',
         'mail_message_identifier', 'received_from', 'received_by',
         'mail_message_created', 'mail_message_sent', 'mail_message_received']
    )

    exchange_event = ExchangeEvent(
        event_group_id=message.get('wm_id'),
        event_type=message.get('type'),
        event_status=message.get('status'),
        event_message=message.get('message'),
        event_exception=message.get('exception'),
        mail_account=message.get('account'),
        event_body=str(message))
    logger.debug('exchange event: %s', exchange_event)

    exchange_message = None
    if message.get('message_uuid', None):
        exchange_message = ExchangeMessage(
            sent_from=message.get('from_email'),
            sent_to=message.get('to_emails'),
            mail_message_identifier=message.get('message_uuid'),
            received_from=message.get('from_address'),
            received_by=message.get('to_addresses'),
            mail_message_created=_parse_datetime(message.get('created')),
            mail_message_sent=_parse_datetime(message.get('sent')),
            mail_message_received=_parse_datetime(message.get('received')))
        logger.debug('exchange message %s', exchange_message)

    return exchange_event, exchange_message


def _parse_datetime(date_time):
    if date_time:
        return parse_datetime(date_time)
    return None
