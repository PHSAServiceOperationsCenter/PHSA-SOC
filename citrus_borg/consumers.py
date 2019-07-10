"""
.. _consumers:

consumers module: functions and classes for consuming AMQP messages sent
by the logstash server (relaying windows events to citrus_borg

:module:    p_soc_auto.orion_integration.apps

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    nov. 16, 2018


message structure
=================

this is the message that is available on the rabbitmq exchange. it is a plain
text representation of the windows event as captured by a winlogbeat service
running on a citrix bot. the exchange receives the messages from all the bots
by way of the logstash server.

**note that this is a string despite the fact that it looks like JSON.**
using the JSON encoder provided by logstash leads to rabbitmq failures.

**However**, converting this string to a JSON structure in the consumer
listed below seems to work and therefore we have not implemented a dedicated
parser for it.

    Note:

        we are using \ as line continuation characters.

message from a successful logon event
-------------------------------------

{"opcode":"Info",
"@version":"1",
"log_name":"Application",
"@timestamp":"2018-11-19T19:09:59.122Z",
"keywords":["Classic"],
"event_data":
    {"param1":"Successful logon: \
    to resource: PMOffice - CST Brokered by device: \
    PHSACDCTX29 \
    \n\nTest Details:\n----------------------\n\
    Latest Test Result: True\
    \nStorefront Connection Time: 00:00:02.4438449\
    \nReceiver Startup: 00:00:01.1075926\
    \nConnection Time: 00:00:00.4127132\
    \nLogon Time: 00:00:06.7571505\
    \nLogoff Time: 00:00:05.3776091"
    },
"tags":["beats_input_codec_plain_applied"],
"level":"Warning",
"computer_name":"baby_d",
"type":"wineventlog",
"beat":{"hostname":"baby_d","version":"6.5.0","name":"baby_d"},

"message": \
"Successful logon: to resource: PMOffice - CST Brokered by device: PHSACDCTX29
          \n
          \nTest Details:
          \n----------------------
          \nLatest Test Result: True
          \nStorefront Connection Time: 00:00:02.4438449\
          \nReceiver Startup: 00:00:01.1075926\
          \nConnection Time: 00:00:00.4127132
          \nLogon Time: 00:00:06.7571505
          \nLogoff Time: 00:00:05.3776091",
"event_id":1000,
"source_name":"ControlUp Logon Monitor",
"host":{
    "name":"baby_d",
    "os":{
        "version":"10.0","platform":"windows","build":"17134.407",
        "family":"windows"
        },
    "ip":["fe80::449b:87fb:5758:b29","169.254.11.41",
          "fe80::bc38:afcd:34ba:8de2",
          "169.254.141.226","fe80::5181:28ba:b614:957a","169.254.149.122",
          "fe80::441f:c81b:f69b:e22b","10.42.27.105",
          "fe80::e947:1c6c:3ce9:ec12","169.254.236.18",
          "fe80::dd4c:609f:d278:2d75",
          "172.24.70.33"],
    "architecture":"x86_64",
    "id":"e4ee2cbd-baa7-4e97-abfc-afd5a8e46730",
    "mac":["02:00:4c:4f:4f:50","9e:b6:d0:8a:23:df","ae:b6:d0:8a:23:df",
           "9c:b6:d0:8a:23:df","9c:b6:d0:8a:23:e0","02:15:03:a1:a2:5e"]
    },
"record_number":"19516"}

the string above is collected from a windows 10 pro host that is not an
official bot host. it has been observed that events collected from official
bots do not include all the info in the **host:** section

"""
import json

from celery.utils.log import get_task_logger
from event_consumer import message_handler

from citrus_borg.dynamic_preferences_registry import get_preference

_logger = get_task_logger(__name__)


@message_handler('logstash', exchange='default')
def process_win_event(body):
    """
    consume AMQP messages sent by the logstash server

    basically it's a callback that gets called every time there is a new
    message placed on the logstash RabbitMQ exchange

    :arg str body: the message; it is a string because the
                   winlogbeat + logstash combination use a plain text coded
                   for the data

    :returns: to be determined
    """
    from .models import AllowedEventSource
    from .tasks import store_borg_data
    from mail_collector.tasks import store_mail_data

    _logger.debug('resistance is futile... now processing %s' % body)

    borg = json.loads(body)
    if borg.get('source_name', None) not in list(
            AllowedEventSource.objects.values_list('source_name', flat=True)):
        _logger.info('%s is not a monitored event source' %
                     borg.get('source_name', None))
        return

    if borg.get('source_name', None) in \
            get_preference('citrusborgevents__source').split(','):
        store_borg_data.delay(borg)

    elif borg.get('source_name', None) in \
            get_preference('exchange__source').split(','):
        store_mail_data.delay(borg)
