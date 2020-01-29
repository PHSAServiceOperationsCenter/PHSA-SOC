"""
.. _assimilation:

Assimilation Module
-------------------

:module:    citrus_borg.locutus.assimilation

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

:updated:    Oct. 9, 2019

This module contains Functions for parsing `Windows` log events delivered via
`AMQP <https://www.amqp.org/>`__ messages to `Python
<https://docs.python.org/3.6/index.html>`__ data structures.

`Windows` log events processed by the functions in this module are created by
the `ControlUp Logon Simulator
<https://www.controlup.com/products/logon-simulator/>`__
or by the :ref:`Mail Borg Client Application`.

:Note:

    If one needs to install `ControlUp` on a `Citrix` client, one must use the
    version stored on the `Sharepoint
    <http://our.healthbc.org/sites/gateway/team/TSCSTHub/Shared Documents"""\
"""/Forms/AllItems.aspx?RootFolder=%2Fsites%2Fgateway%2Fteam%2FTSCSTHub%2F"""\
"""Shared Documents%2FTools%2FControlUp&FolderCTID="""\
"""0x01200049BD2FC3E2032F40A74A4A7D97D53F7A&View="""\
"""{C5878F2F-ACBC-450F-AF48-52726B6E8F63}>`__
    server.

Here is a sample for a `Windows` event created by `ControlUp` in the format
that will be consumed by the :func:`citrus_borg.consumers.process_win_event`
function.

:Note:
    **This message is a string despite the fact that it looks like**
    `JSON <https://www.json.org/>`__. Using the `JSON` encoder provided by the
    :ref:`Logstash server` will lead to :ref:`RabbitMQ Server` failures.
    However, the :func:`json.loads` function is happy to deserialize this string
    to a `Python` `object` without any problems.

We are converting the message to a `JSON` structure in the
:func:`citrus_borg.consumers.process_win_event` function.

`Windows` log events produced by the :ref:`Mail Borg Client Application` are
very similar to the message below.

The most relevant parts of a `Windows` log event as far as we are concerned are
under the

* **message:** key

  This key contains the main data passed from the application to the
  consumer

* **host:** key

  This key contains detailed information about the source of the event

* **source_name:** key

  The value of this key will determine which parser will be used to collect
  the event data

.. code-block:: json

    {\"opcode\":\"Info\",
    \"@version\":\"1\",
    \"log_name\":\"Application\",
    \"@timestamp\":\"2018-11-19T19:09:59.122Z\",
    \"keywords\":[\"Classic\"],
    \"event_data\":
        {\"param1\":\"Successful logon: to resource: PMOffice - CST """\
    """Brokered by device: PHSACDCTX29
        \\n\\nTest Details:\\n----------------------\\n
        Latest Test Result: True
        \\nStorefront Connection Time: 00:00:02.4438449
        \\nReceiver Startup: 00:00:01.1075926
        \\nConnection Time: 00:00:00.4127132
        \\nLogon Time: 00:00:06.7571505
        \\nLogoff Time: 00:00:05.3776091\"
        },
    \"tags\":[\"beats_input_codec_plain_applied\"],
    \"level\":\"Warning\",
    \"computer_name\":\"baby_d\",
    \"type\":\"wineventlog\",
    \"beat\":{\"hostname\":\"baby_d\",\"version\":\"6.5.0\",\"name\":"""\
    """\"baby_d\"},
    \"message\": \
    \"Successful logon: to resource: PMOffice - CST Brokered by device: """\
    """PHSACDCTX29
              \\n
              \\nTest Details:
              \\n----------------------
              \\nLatest Test Result: True
              \\nStorefront Connection Time: 00:00:02.4438449\
              \\nReceiver Startup: 00:00:01.1075926\
              \\nConnection Time: 00:00:00.4127132
              \\nLogon Time: 00:00:06.7571505
              \\nLogoff Time: 00:00:05.3776091\",
    \"event_id\":1000,
    \"source_name\":\"ControlUp Logon Monitor\",
    \"host\":{
        \"name\":\"baby_d\",
        \"os\":{
            \"version\":\"10.0\",\"platform\":\"windows\",\"build\":"""\
    """\"17134.407\",
            \"family\":\"windows\"
            },
        \"ip\":[\"fe80::449b:87fb:5758:b29\",\"169.254.11.41\",
              \"fe80::bc38:afcd:34ba:8de2\",
              \"169.254.141.226\",\"fe80::5181:28ba:b614:957a\","""\
    """\"169.254.149.122\",
              \"fe80::441f:c81b:f69b:e22b\",\"10.42.27.105\",
              \"fe80::e947:1c6c:3ce9:ec12\",\"169.254.236.18\",
              \"fe80::dd4c:609f:d278:2d75\",
              \"172.24.70.33\"],
        \"architecture\":\"x86_64\",
        \"id\":\"e4ee2cbd-baa7-4e97-abfc-afd5a8e46730\",
        \"mac\":[\"02:00:4c:4f:4f:50\",\"9e:b6:d0:8a:23:df\","""\
    """\"ae:b6:d0:8a:23:df\",
               \"9c:b6:d0:8a:23:df\",\"9c:b6:d0:8a:23:e0\","""\
    """\"02:15:03:a1:a2:5e\"]
        },
    \"record_number\":\"19516\"}


This message was collected from a windows 10 pro host that is not an
official bot. It has been observed that events collected from official
bots do not include all the info in the **host:** section.

"""
import collections
import json
from logging import getLogger
import socket

from django.utils.dateparse import parse_duration, parse_datetime

from citrus_borg.dynamic_preferences_registry import get_list_preference

LOG = getLogger(__name__)


def get_ip_for_host_name(host_name, ip_list=None):
    """
    :returns: the IP address that goes with a known host name if it can be
        resolved or `None` otherwise

    :arg str host_name: the host name as reported from external sources

    :arg list ip_list: a list of ip addresses for the host

    :raises:

        :exc:`ValueError` if the `host_name` is missing

    This function loops through the items in the `ip_list` :class:`list`
    argument and returns the one that will resolve to the value of the
    `host_name` argument. The function uses :func:`socket.gethostbyaddr` to
    retrieve the resolved host for each item in the `ip_list` :class:`list`.
    If the resolved host matches the value of the `host_name`, the item in the
    `list` is the `IP` address that we are looking for.
    """
    def _get_host_by_name():
        """
        this is the fall-back function for :func:`get_ip_for_host_name`

        Sometimes there are no entries in the :class:`ip-list <list>`. We will
        try to resolve the `host_name` argument using the
        :func:`socket.gethostbyname` function. If that is not possible,
        we will return`None`.
        """
        try:
            return socket.gethostbyname(host_name)
        except:
            return None

    if host_name is None:
        raise ValueError('host_name argument is mandatory')

    host_name = str(host_name)

    if ip_list is None or not isinstance(ip_list, (list, tuple)):
        return _get_host_by_name()

    for ip_address in ip_list:
        try:
            host_names, _, _ = socket.gethostbyaddr(ip_address)
        except (socket.herror, socket.gaierror) as err:
            LOG.info('Could not resolve %s to host names: %s',
                     ip_address, err)
            continue

        if host_name in host_names:
            LOG.info('%s resolved to %s', host_name, ip_address)
            return ip_address
        LOG.debug('%s resolved to %s, which do not include %s',
                  ip_address, host_names, host_name)

    return _get_host_by_name()


def process_borg(body=None):
    """
    :returns: a :func:`collections.namedtuple` object

    :arg dict body: the `Windows` message after it was deserialized from `JSON`
        in the :func:`citrus_borg.consumers.process_win_event` function

    The `Borg` `object` has the following properties: `source_host`,
    `record_number`, `opcode`, `level`, `event_source`, `windows_log`,
    `borg_message`, `mail_borg_message`.

    This function is invoking the parsers that will generate easy to save
    `Python` objects.

    The `event_source` property will determine which application is the
    destination of the `Windows` `event`.
    """
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

    if borg.event_source in get_list_preference('citrusborgevents__source'):
        borg.borg_message = process_borg_message(body.get('message', None))
        borg.mail_borg_message = None
    elif borg.event_source in get_list_preference('exchange__source'):
        borg.borg_message = None
        borg.mail_borg_message = process_exchange_message(
            json.loads(body.get('event_data')['param1'])
        )

    return borg


def process_borg_host(host=None):
    """
    prepare a `Python` object representing the bot host

    The `BorgHost` object has he following properties: `host_name`, and
    `ip_address`.

    The `BorgHost` object will be saved in the :ref:`Citrus Borg Application`
    and shared with the :ref:`Mail Collector Application`.

    :returns: a :func:`collections.namedtuple` representation of the host
        information for a remote monitoring bot

    The raw data is available under the **host:** key of the `event`
    :class:`dictionary <dict>` and it looks like this:

    .. code-block:: json-object

        "host": "{
            'name': 'baby_d',
            'mac': ['02:00:4c:4f:4f:50', '9e:b6:d0:8a:23:df',
                    'ae:b6:d0:8a:23:df', '9c:b6:d0:8a:23:df',
                    '9c:b6:d0:8a:23:e0', '02:15:03:a1:a2:5e'],
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
        }"


    """
    if host is None:
        raise ValueError('host argument is mandatory')

    borg_host = collections.namedtuple(
        'BorgHost', ['host_name', 'ip_address', ])

    borg_host.host_name = host.get('name', None)
    borg_host.ip_address = get_ip_for_host_name(host.get('name', None),
                                                host.get('ip', None))

    return borg_host


# TODO refactor this
def process_borg_message(message=None):
    """
    prepare a `Python` object representing a `ControlUp` event

    This function is used by the :ref:`Citrus Borg Application`.

    This is a successful `ControlUp` event::

        Successful logon: to resource: PMOffice - CST Brokered by device: """\
    """PHSACDCTX42

        Test Details:
        \\----------------------
        Latest Test Result: True
        Storefront Connection Time: 00:00:03.1083110
        Receiver Startup: 00:00:01.1673405
        Connection Time: 00:00:00.4353095
        Logon Time: 00:00:04.0380058
        Logoff Time: 00:00:05.3581214


    This is a failed `ControlUp` event::

        Failed logon to resource: PMOffice - CST
        Failure reason: The Connection failed during session logon.
        Failure details:

        Test Output:
        \\----------------------
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


    :arg dict message: the event message

    :arg logger: the logging object
    :type logger: :class:`logging.Logger`

    :returns: a :func:`collections.namedtuple` object representing the
        `ControlUp` event

        The `BorgMessage` object has the following properties: 'state',
        `broker`, `test_result`, `storefront_connection_duration`,
        `receiver_startup_duration`, `connection_achieved_duration`,
        `logon_achieved_duration`, `logoff_achieved_duration`, `failure_reason`,
        `failure_details`, `raw_message`

    .. todo::

        In case the message is `None`, create a dynamic preference for the
        raw_message property of the `namedtuple`.

    """
    borg_message = collections.namedtuple(
        'BorgMessage', [
            'state', 'broker', 'test_result', 'storefront_connection_duration',
            'receiver_startup_duration', 'connection_achieved_duration',
            'logon_achieved_duration', 'logoff_achieved_duration',
            'failure_reason', 'failure_details', 'raw_message'
        ]
    )

    if message is None:
        # this is an error case
        LOG.error('a message was not provided with this event')
        borg_message.raw_message = 'a message was not provided with this event'
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

    borg_message.raw_message = str(message)
    message = message.split('\n')
    borg_message.state = message[0].split()[0]

    if borg_message.state.lower() in ['successful']:
        LOG.debug('citrus borg event state: successful')
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
        LOG.debug('citrus borg event state: failed')
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
        LOG.error('citrus borg event state undetermined %s',
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


def process_exchange_message(message):
    """
    prepare a `Python` object representing a `Mail Borg` event

    This function is used by the :ref:`Mail Collector Application`.

    `Mail Borg` events are represented by a :class:`dictionary <dict>`.

    :arg dict message: the event message

    :returns: a :class:`tuple` containing a pair of
        :func:`collections.namedtuple` objects that describe the
        `Mail Borg` event

        The `ExchangeEvent` object is the first member of the :class:`tuple` and
        represents the identification part of a `Mail Borg` event. It has the
        following properties: `event_group_id`, `event_type`, `event_status`,
        `event_message`, `event_exception`, `mail_account`, `event_body`. This
        information is generated for all `Mail Borg` events.

        The `ExchangeMessage` object is the second member of the :class:`tuple`
        and it represents events associated not only with the :ref:`Mail Borg
        Client Application` operations but also with specific `Exchange`
        messages. Such events are only created when sending and receiving
        `Exchange` messages. The `ExchangeMessage` object has the following
        properties: `sent_from`, `sent_to`, `mail_message_identifier`,
        `received_from`, `received_by`, `mail_message_created`,
        `mail_message_sent`, `mail_message_received`
    """
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
    LOG.debug('exchange event: %s', exchange_event)

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
        LOG.debug('exchange message %s', exchange_message)

    return exchange_event, exchange_message


def _parse_datetime(date_time=None):
    """
    parse a string representation of date-time to a :class:`datetime.datetime`
    object

    :arg str date_time: a date-time value or `None`

    :returns: a :class:`datetime.datetime` object or `None`

    """
    if date_time:
        return parse_datetime(date_time)
    return None
