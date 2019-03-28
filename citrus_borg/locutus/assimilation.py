"""
.. _assimilation:

functions and classes for uploading windows events to the citrus_borg app

:module:    citrus_borg.locutus.assimilation

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    nov. 128, 2018

"""
import collections
import socket

from django.utils.dateparse import parse_duration


def get_ip_for_host_name(host_name=None, ip_list=None):
    """
    :returns: the IP address that goes with a known host name or ``None``

    :arg str host_name: the host name as reported from external sources

    :arg list ip_list: a list of ip addresses for a host as returned from
                       external sources

    :raises:

        :exception:`<ValueError>` if either argument is missing

        :exception:`<TypeError>` if ip_list is not a ``list`` or ``tuple``

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

    the function loops through the :arg:`<ip_list>` and returns
    the one ip address that resolves to the :arg:`<host_name>`

    """
    def _gethostbyname():
        """
        the contortions below are to deal with multiple ip addresses
        as returned by winlogbeat

        but sometimes one needs to KISS the principle
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


def process_borg(body=None):
    """
    :returns; a ``colections.namedtuple`` object with all the properties of
    the event log body
    """
    if body is None:
        raise ValueError('body argument is mandatory')

    borg = collections.namedtuple(
        'Borg', [
            'source_host', 'record_number', 'opcode', 'level',
            'event_source', 'windows_log', 'borg_message'
        ]
    )

    borg.source_host = process_borg_host(body.get('host', None))
    borg.record_number = body.get('record_number', 0)
    borg.opcode = body.get('opcode', None)
    borg.level = body.get('level', None)
    borg.event_source = body.get('source_name', None)
    borg.windows_log = body.get('log_name', None)
    borg.borg_message = process_borg_message(body.get('message', None))

    return borg


def process_borg_host(host=None):
    """
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


def process_borg_message(message=None):
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
