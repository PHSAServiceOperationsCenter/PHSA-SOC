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

"""
import json

from celery.utils.log import get_task_logger
from event_consumer import message_handler

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

    _logger.debug('resistance is futile... now processing %s' % body)

    borg = json.loads(body)
    if borg.get('sorce_name', None) not in list(
            AllowedEventSource.objects.values_list('sorce_name', flat=True)):
        _logger.info('%s is not a monitored event source' %
                     borg.get('sorce_name', None))
        return

    store_borg_data.delay(borg)


"""

dict_keys(['computer_name', 'tags', 'beat', 'keywords', '@timestamp', 'type', '@version', 'event_id', 'event_data', 'record_number', 'level', 'opcode', 'message', 'source_name', 'host', 'log_name'])
computer_name:   baby_d
tags:    ['beats_input_codec_plain_applied']
beat:    {'name': 'baby_d', 'version': '6.5.0', 'hostname': 'baby_d'}
keywords:        ['Classic']
@timestamp:      2018-11-19T20:08:20.688Z
type:    wineventlog
@version:        1
event_id:        1000
event_data:      {'param1': 'Successful logon: to resource: PMOffice - CST Brokered by device: PHSACDCTX07\n\nTest Details:\n----------------------\nLatest Test Result: True\nStorefront Connection Time: 00:00:03.2385044\nReceiver Startup: 00:00:01.0777563\nConnection Time: 00:00:00.4130755\nLogon Time: 00:00:03.9544909\nLogoff Time: 00:00:05.3478382'}
record_number:   19541
level:   Warning
opcode:  Info
message: Successful logon: to resource: PMOffice - CST Brokered by device: PHSACDCTX07

Test Details:
----------------------
Latest Test Result: True
Storefront Connection Time: 00:00:03.2385044
Receiver Startup: 00:00:01.0777563
Connection Time: 00:00:00.4130755
Logon Time: 00:00:03.9544909
Logoff Time: 00:00:05.3478382

source_name:     ControlUp Logon Monitor
host:    {
    'name': 'baby_d', 
    'mac': ['02:00:4c:4f:4f:50', '9e:b6:d0:8a:23:df', 'ae:b6:d0:8a:23:df', '9c:b6:d0:8a:23:df', '9c:b6:d0:8a:23:e0', '02:15:03:a1:a2:5e'], 
    'ip': ['fe80::449b:87fb:5758:b29', '169.254.11.41', 'fe80::bc38:afcd:34ba:8de2', '169.254.141.226', 'fe80::5181:28ba:b614:957a', '169.254.149.122', 'fe80::441f:c81b:f69b:e22b', '10.42.27.105', 'fe80::e947:1c6c:3ce9:ec12', '169.254.236.18', 'fe80::dd4c:609f:d278:2d75', '172.24.70.33'], 
    'id': 'e4ee2cbd-baa7-4e97-abfc-afd5a8e46730', 
    'architecture': 'x86_64', 
    'os': {'version': '10.0', 'build': '17134.407', 'platform': 'windows', 'family': 'windows'}}
log_name:        Application





[2018-11-19 11:10:55,067: WARNING/MainProcess] 
{"opcode":"Info",
"@version":"1",
"log_name":"Application",
"@timestamp":"2018-11-19T19:09:59.122Z",
"keywords":["Classic"],
"event_data":
    {"param1":"Successful logon: to resource: PMOffice - CST Brokered by device: PHSACDCTX29\n\nTest Details:\n----------------------\nLatest Test Result: True\nStorefront Connection Time: 00:00:02.4438449\nReceiver Startup: 00:00:01.1075926\nConnection Time: 00:00:00.4127132\nLogon Time: 00:00:06.7571505\nLogoff Time: 00:00:05.3776091"
    },
"tags":["beats_input_codec_plain_applied"],
"level":"Warning",
"computer_name":"baby_d",
"type":"wineventlog",
"beat":{"hostname":"baby_d","version":"6.5.0","name":"baby_d"},

"message":"Successful logon: to resource: PMOffice - CST Brokered by device: PHSACDCTX29
          \n
          \nTest Details:
          \n----------------------
          \nLatest Test Result: True
          \nStorefront Connection Time: 00:00:02.4438449\nReceiver Startup: 00:00:01.1075926\nConnection Time: 00:00:00.4127132
          \nLogon Time: 00:00:06.7571505
          \nLogoff Time: 00:00:05.3776091",
"event_id":1000,
"source_name":"ControlUp Logon Monitor",
"host":{
    "name":"baby_d",
    "os":{
        "version":"10.0","platform":"windows","build":"17134.407","family":"windows"
        },
    "ip":["fe80::449b:87fb:5758:b29","169.254.11.41","fe80::bc38:afcd:34ba:8de2",
          "169.254.141.226","fe80::5181:28ba:b614:957a","169.254.149.122",
          "fe80::441f:c81b:f69b:e22b","10.42.27.105",
          "fe80::e947:1c6c:3ce9:ec12","169.254.236.18","fe80::dd4c:609f:d278:2d75",
          "172.24.70.33"],
    "architecture":"x86_64",
    "id":"e4ee2cbd-baa7-4e97-abfc-afd5a8e46730",
    "mac":["02:00:4c:4f:4f:50","9e:b6:d0:8a:23:df","ae:b6:d0:8a:23:df",
           "9c:b6:d0:8a:23:df","9c:b6:d0:8a:23:e0","02:15:03:a1:a2:5e"]
    },
"record_number":"19516"}
"""
