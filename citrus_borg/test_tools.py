from time import sleep

from citrus_borg.tasks import process_citrix_login
from citrus_borg.dynamic_preferences_registry import get_int_list_preference

from random import choice
from datetime import datetime, timezone

# TODO fix formatting of this dict
FAILURE_EXAMPLE = {
    'host': {
        'architecture': 'x86_64',
        'ip': ['fe80::fc8c:6b8:65fb:3d84', '10.21.179.4',
            'fe80::5efe:a15:b304'],
        'os': {
            'version': '6.1',
            'family': 'windows',
            'build': '7601.24544',
            'platform': 'windows'
        },
        'mac': ['50:7b:9d:03:3c:a7', '00:00:00:00:00:00:00:e0'],
        'name': 'BCCSS-T450S-04',
        'id': 'd7defb07-3a34-4bfd-b2b5-360daa5a549f'
    },
    '@timestamp': '2020-02-24T23:19:53.000Z',
    'record_number': '1770593',
    'opcode': 'Info',
    'log_name': 'Application',
    'source_name': 'ControlUp Logon Monitor',
    '@version': '1',
    # Edited event id to make it an actual failure for our classification
    'event_id': 1006,
    'beat': {
        'version': '6.5.1',
        'hostname': 'BCCSS-T450S-04',
        'name': 'BCCSS-T450S-04'
    },
    'event_data': {
        'param1': 'Failed logon to resource: PMOffice - CST\nFailure '
                  'reason: The Connection failed during session logoff.'
                  ' \nFailure details:   a timeout or disconnect was '
                  'caught: A timeout was reached.\nDevice: PHSACDCTX144'
                  '\nTest Output:\n----------------------\n3:15:49 PM -'
                  ' Starting storefront connection\n3:15:49 PM -'
                  ' Initialising storefront\n3:15:49 PM - Requesting'
                  ' resources\n3:15:51 PM - Received resources\n3:15:51'
                  ' PM - Resource found, requesting ICA file\n3:15:52'
                  ' PM - Connecting to: 104.170.202.235:1494\n3:15:52'
                  ' PM - ICA file received\n3:15:52 PM - Initialising '
                  'received\n3:15:53 PM - Connecting received\n3:15:53'
                  ' PM - Connect received\n3:15:55 PM - New desktop '
                  'info received\n3:16:00 PM - Successfully logged onto'
                  ' device: PHSACDCTX144 .\n3:16:00 PM - Logon '
                  'successful, sleeping for 60 seconds\n3:16:00 PM - '
                  'Roundtrip time was 66ms\n3:17:00 PM - Log off '
                  'requested\n3:19:52 PM - A timeout occurred!\n3:19:52'
                  ' PM - Total connection time: 0\n3:19:52 PM - Forcing'
                  ' a disconnect\n3:19:52 PM - Test will start again'
                  ' in: 180 seconds'
    },
    'level': 'Error',
    'tags': ['beats_input_codec_plain_applied'],
    'keywords': ['Classic'],
    'computer_name': 'BCCSS-T450S-04.HealthBC.org',
    'message': 'Failed logon to resource: PMOffice - CST\nFailure reason: '
               'The Connection failed during session logoff. \nFailure '
               'details:   a timeout or disconnect was caught: A timeout '
               'was reached.\nDevice: PHSACDCTX144\nTest Output:\n'
               '----------------------\n3:15:49 PM - Starting storefront '
               'connection\n3:15:49 PM - Initialising storefront\n3:15:49 '
               'PM - Requesting resources\n3:15:51 PM - Received resources'
               '\n3:15:51 PM - Resource found, requesting ICA file\n3:15:52'
               ' PM - Connecting to: 104.170.202.235:1494\n3:15:52 PM - ICA'
               ' file received\n3:15:52 PM - Initialising received\n3:15:53'
               ' PM - Connecting received\n3:15:53 PM - Connect received\n'
               '3:15:55 PM - New desktop info received\n3:16:00 PM - '
               'Successfully logged onto device: PHSACDCTX144 .\n3:16:00 PM'
               ' - Logon successful, sleeping for 60 seconds\n3:16:00 PM - '
               'Roundtrip time was 66ms\n3:17:00 PM - Log off requested\n'
               '3:19:52 PM - A timeout occurred!\n3:19:52 PM - Total '
               'connection time: 0\n3:19:52 PM - Forcing a disconnect\n'
               '3:19:52 PM - Test will start again in: 180 seconds',
    'type': 'wineventlog'
}

IGNORE_FAILURE_EXAMPLE = {
    'host': {
        'architecture': 'x86_64',
        'ip': ['fe80::fc8c:6b8:65fb:3d84', '10.21.179.4',
            'fe80::5efe:a15:b304'],
        'os': {
            'version': '6.1',
            'family': 'windows',
            'build': '7601.24544',
            'platform': 'windows'
        },
        'mac': ['50:7b:9d:03:3c:a7', '00:00:00:00:00:00:00:e0'],
        'name': 'BCCSS-T450S-04',
        'id': 'd7defb07-3a34-4bfd-b2b5-360daa5a549f'
    },
    '@timestamp': '2020-02-24T23:19:53.000Z',
    'record_number': '1770593',
    'opcode': 'Info',
    'log_name': 'Application',
    'source_name': 'ControlUp Logon Monitor',
    '@version': '1',
    'event_id': 1018,
    'beat': {
        'version': '6.5.1',
        'hostname': 'BCCSS-T450S-04',
        'name': 'BCCSS-T450S-04'
    },
    'event_data': {
        'param1': 'Failed logon to resource: PMOffice - CST\nFailure '
                  'reason: The Connection failed during session logoff.'
                  ' \nFailure details:   a timeout or disconnect was '
                  'caught: A timeout was reached.\nDevice: PHSACDCTX144'
                  '\nTest Output:\n----------------------\n3:15:49 PM -'
                  ' Starting storefront connection\n3:15:49 PM -'
                  ' Initialising storefront\n3:15:49 PM - Requesting'
                  ' resources\n3:15:51 PM - Received resources\n3:15:51'
                  ' PM - Resource found, requesting ICA file\n3:15:52'
                  ' PM - Connecting to: 104.170.202.235:1494\n3:15:52'
                  ' PM - ICA file received\n3:15:52 PM - Initialising '
                  'received\n3:15:53 PM - Connecting received\n3:15:53'
                  ' PM - Connect received\n3:15:55 PM - New desktop '
                  'info received\n3:16:00 PM - Successfully logged onto'
                  ' device: PHSACDCTX144 .\n3:16:00 PM - Logon '
                  'successful, sleeping for 60 seconds\n3:16:00 PM - '
                  'Roundtrip time was 66ms\n3:17:00 PM - Log off '
                  'requested\n3:19:52 PM - A timeout occurred!\n3:19:52'
                  ' PM - Total connection time: 0\n3:19:52 PM - Forcing'
                  ' a disconnect\n3:19:52 PM - Test will start again'
                  ' in: 180 seconds'
    },
    'level': 'Error',
    'tags': ['beats_input_codec_plain_applied'],
    'keywords': ['Classic'],
    'computer_name': 'BCCSS-T450S-04.HealthBC.org',
    'message': 'Failed logon to resource: PMOffice - CST\nFailure reason: '
               'The Connection failed during session logoff. \nFailure '
               'details:   a timeout or disconnect was caught: A timeout '
               'was reached.\nDevice: PHSACDCTX144\nTest Output:\n'
               '----------------------\n3:15:49 PM - Starting storefront '
               'connection\n3:15:49 PM - Initialising storefront\n3:15:49 '
               'PM - Requesting resources\n3:15:51 PM - Received resources'
               '\n3:15:51 PM - Resource found, requesting ICA file\n3:15:52'
               ' PM - Connecting to: 104.170.202.235:1494\n3:15:52 PM - ICA'
               ' file received\n3:15:52 PM - Initialising received\n3:15:53'
               ' PM - Connecting received\n3:15:53 PM - Connect received\n'
               '3:15:55 PM - New desktop info received\n3:16:00 PM - '
               'Successfully logged onto device: PHSACDCTX144 .\n3:16:00 PM'
               ' - Logon successful, sleeping for 60 seconds\n3:16:00 PM - '
               'Roundtrip time was 66ms\n3:17:00 PM - Log off requested\n'
               '3:19:52 PM - A timeout occurred!\n3:19:52 PM - Total '
               'connection time: 0\n3:19:52 PM - Forcing a disconnect\n'
               '3:19:52 PM - Test will start again in: 180 seconds',
    'type': 'wineventlog'
}

PASS_EXAMPLE = {
    'host': {
        'architecture': 'x86_64',
        'ip': ['fe80::fc8c:6b8:65fb:3d84', '10.21.179.4',
            'fe80::5efe:a15:b304'],
        'os': {
            'version': '6.1',
            'family': 'windows',
            'build': '7601.24544',
            'platform': 'windows'
        },
        'mac': ['50:7b:9d:03:3c:a7', '00:00:00:00:00:00:00:e0'],
        'name': 'BCCSS-T450S-04',
        'id': 'd7defb07-3a34-4bfd-b2b5-360daa5a549f'
    },
    '@timestamp': '2020-02-24T23:19:53.000Z',
    'record_number': '1770593',
    'opcode': 'Info',
    'log_name': 'Application',
    'source_name': 'ControlUp Logon Monitor',
    '@version': '1',
    # Edited event id to make it an actual failure for our classification
    'event_id': 1000,
    'beat': {
        'version': '6.5.1',
        'hostname': 'BCCSS-T450S-04',
        'name': 'BCCSS-T450S-04'
    }, # TODO should edit message to actually be a pass
    'event_data': {
        'param1': 'Failed logon to resource: PMOffice - CST\nFailure '
                  'reason: The Connection failed during session logoff.'
                  ' \nFailure details:   a timeout or disconnect was '
                  'caught: A timeout was reached.\nDevice: PHSACDCTX144'
                  '\nTest Output:\n----------------------\n3:15:49 PM -'
                  ' Starting storefront connection\n3:15:49 PM -'
                  ' Initialising storefront\n3:15:49 PM - Requesting'
                  ' resources\n3:15:51 PM - Received resources\n3:15:51'
                  ' PM - Resource found, requesting ICA file\n3:15:52'
                  ' PM - Connecting to: 104.170.202.235:1494\n3:15:52'
                  ' PM - ICA file received\n3:15:52 PM - Initialising '
                  'received\n3:15:53 PM - Connecting received\n3:15:53'
                  ' PM - Connect received\n3:15:55 PM - New desktop '
                  'info received\n3:16:00 PM - Successfully logged onto'
                  ' device: PHSACDCTX144 .\n3:16:00 PM - Logon '
                  'successful, sleeping for 60 seconds\n3:16:00 PM - '
                  'Roundtrip time was 66ms\n3:17:00 PM - Log off '
                  'requested\n3:19:52 PM - A timeout occurred!\n3:19:52'
                  ' PM - Total connection time: 0\n3:19:52 PM - Forcing'
                  ' a disconnect\n3:19:52 PM - Test will start again'
                  ' in: 180 seconds'
    },
    'level': 'Info',
    'tags': ['beats_input_codec_plain_applied'],
    'keywords': ['Classic'],
    'computer_name': 'BCCSS-T450S-04.HealthBC.org',
    'message': 'Failed logon to resource: PMOffice - CST\nFailure reason: '
               'The Connection failed during session logoff. \nFailure '
               'details:   a timeout or disconnect was caught: A timeout '
               'was reached.\nDevice: PHSACDCTX144\nTest Output:\n'
               '----------------------\n3:15:49 PM - Starting storefront '
               'connection\n3:15:49 PM - Initialising storefront\n3:15:49 '
               'PM - Requesting resources\n3:15:51 PM - Received resources'
               '\n3:15:51 PM - Resource found, requesting ICA file\n3:15:52'
               ' PM - Connecting to: 104.170.202.235:1494\n3:15:52 PM - ICA'
               ' file received\n3:15:52 PM - Initialising received\n3:15:53'
               ' PM - Connecting received\n3:15:53 PM - Connect received\n'
               '3:15:55 PM - New desktop info received\n3:16:00 PM - '
               'Successfully logged onto device: PHSACDCTX144 .\n3:16:00 PM'
               ' - Logon successful, sleeping for 60 seconds\n3:16:00 PM - '
               'Roundtrip time was 66ms\n3:17:00 PM - Log off requested\n'
               '3:19:52 PM - A timeout occurred!\n3:19:52 PM - Total '
               'connection time: 0\n3:19:52 PM - Forcing a disconnect\n'
               '3:19:52 PM - Test will start again in: 180 seconds',
    'type': 'wineventlog'
}

FAIL_MSG = ('Failed logon to resource: PMOffice - CST\nFailure reason: '
            'The Connection failed during session logoff. \nFailure '
            'details:   a timeout or disconnect was caught: A timeout '
            'was reached.\nDevice: PHSACDCTX144\nTest Output:\n'
            '----------------------\n3:15:49 PM - Starting storefront '
            'connection\n3:15:49 PM - Initialising storefront\n3:15:49 '
            'PM - Requesting resources\n3:15:51 PM - Received resources'
            '\n3:15:51 PM - Resource found, requesting ICA file\n3:15:52'
            ' PM - Connecting to: 104.170.202.235:1494\n3:15:52 PM - ICA'
            ' file received\n3:15:52 PM - Initialising received\n3:15:53'
            ' PM - Connecting received\n3:15:53 PM - Connect received\n'
            '3:15:55 PM - New desktop info received\n3:16:00 PM - '
            'Successfully logged onto device: PHSACDCTX144 .\n3:16:00 PM'
            ' - Logon successful, sleeping for 60 seconds\n3:16:00 PM - '
            'Roundtrip time was 66ms\n3:17:00 PM - Log off requested\n'
            '3:19:52 PM - A timeout occurred!\n3:19:52 PM - Total '
            'connection time: 0\n3:19:52 PM - Forcing a disconnect\n'
            '3:19:52 PM - Test will start again in: 180 seconds')
PASS_MSG = ('Successful logon: to resource: PMOffice - CST Brokered by device: '
            'PHSACDCTX36\n\nTest Details:\n----------------------\nLatest Test '
            'Result: True\nStorefront Connection Time: 00:00:03.0478000\n'
            'Receiver Startup: 00:00:00.7342000\nConnection Time: '
            '00:00:00.8600000\nLogon Time: 00:00:04.6392000\nLogoff Time: '
            '00:00:06.5454000')

LD038075 = {
    'architecture': 'x86_64',
    'ip': ['169.254.80.184', '169.254.129.89', '10.42.210.59', '10.21.175.98'],
    'os': {
        'build': '7601.24540',
        'family': 'windows',
        'platform': 'windows',
        'version': '6.1'
    },
    'mac': ['62:f6:77:14:39:3f', '62:f6:77:14:39:40', '60:f6:77:14:39:3f',
            '54:e1:ad:dc:fc:b3'],
    'name': 'LD038075',
    'id': '22049b21-64b6-446a-8461-94a16ead4149'
}

BCCSST450S04 = {
    'architecture': 'x86_64',
    'ip': ['fe80::fc8c:6b8:65fb:3d84', '10.21.179.4', 'fe80::5efe:a15:b304'],
    'os': {
        'version': '6.1',
        'family': 'windows',
        'build': '7601.24544',
        'platform': 'windows'
    },
    'mac': ['50:7b:9d:03:3c:a7', '00:00:00:00:00:00:00:e0'],
    'name': 'BCCSS-T450S-04',
    'id': 'd7defb07-3a34-4bfd-b2b5-360daa5a549f'
}

LD031147 = {
    'architecture': 'x86_64',
    'ip': ['fe80::d0fb:554f:a9fb:a327', '169.254.163.39',
           'fe80::b494:72ef:4e60:694b', '172.24.66.178', 'fe80::5efe:ac18:42b2',
           'fe80::5efe:a9fe:a327'],
    'os': {
        'build': '7601.24544',
        'version': '6.1',
        'platform': 'windows',
        'family': 'windows'
    },
    'mac': ['02:00:4c:4f:4f:50', '28:d2:44:c2:c3:3b', '00:00:00:00:00:00:00:e0',
            '00:00:00:00:00:00:00:e0'],
    'name': 'LD021147',
    'id': 'a06d5df7-2f52-4d0e-8b6e-4bf958ac0b1a'
}

HOSTS = [LD038075, BCCSST450S04, LD031147]


def generate_failure():
    return generate_example(True,
        choice(get_int_list_preference('citrusborgux__cluster_event_ids')),
        str(datetime.now(timezone.utc)), choice(HOSTS))

def generate_success():
    return generate_example(False, choice([1000, 1020, 1003, 500]),
                            str(datetime.now(timezone.utc)), choice(HOSTS))


def generate_example(failed, id_num, timestamp, host):
    msg = PASS_MSG
    level = 'Warning'
    if failed:
        msg = FAIL_MSG
        level = 'Error'

    output = {
        'host': host,
        '@timestamp': timestamp,
        'record_number': '1770593',
        'opcode': 'Info',
        'log_name': 'Application',
        'source_name': 'ControlUp Logon Monitor',
        '@version': '1',
        'event_id': id_num,
        'beat': {
            'version': '6.5.1',
            'hostname': 'BCCSS-T450S-04',
            'name': 'BCCSS-T450S-04'
        },
        'event_data': {
            'param1': msg,
        },
        'level': level,
        'tags': ['beats_input_codec_plain_applied'],
        'keywords': ['Classic'],
        'computer_name': 'BCCSS-T450S-04.HealthBC.org',
        'message': msg,
        'type': 'wineventlog'
    }
    return output


def keep_on_generating():
    while True:
        process_citrix_login(choice([generate_failure, generate_success])())
        sleep(5)
