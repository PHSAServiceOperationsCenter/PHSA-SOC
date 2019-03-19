"""
.. _models:

django models for the ssl_certificates app

:module:    db_helper.py

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""
import logging
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from ssl_cert_tracker.models import NmapCertsData

logging.basicConfig(filename='p_soc_auto.log', level=logging.DEBUG)


def insert_into_certs_data(json_data):
    """
    create or update instances of :class:`<models.NmapCertsData>`
     """

    NmapCertsData.created_by = NmapCertsData.get_or_create_user(
        username='PHSA_User')

    qs = NmapCertsData.objects.filter(md5=json_data['md5'])
    if qs.exists():
        db_certs = qs.get()
        db_certs.last_updated = timezone.now()
        db_certs.save()
        return

    db_certs = NmapCertsData()
    db_certs.node_id = json_data["node_id"]
    db_certs.addresses = json_data["addresses"]
    db_certs.created_by_id = NmapCertsData.created_by.id
    db_certs.updated_by_id = NmapCertsData.created_by.id

    db_certs.not_before = _make_aware(parse_datetime(json_data["not_before"]))

    db_certs.not_after = _make_aware(parse_datetime(json_data["not_after"]))

    db_certs.common_name = json_data["common_name"]
    db_certs.organization_name = json_data["organization_name"]
    # TO DO
    #db_certs.organizational_unit_name = json_data["organizational_unit_name"]
    db_certs.country_name = json_data["country_name"]
    db_certs.sig_algo = json_data["sig_algo"]
    db_certs.name = json_data["name"]
    db_certs.bits = json_data["bits"]
    db_certs.md5 = json_data["md5"]
    db_certs.sha1 = json_data["sha1"]
    db_certs.xml_data = json_data["xml_data"]
    db_certs.save()

    return


def _make_aware(datetime_input, use_timezone=timezone.utc, is_dst=False):
    """
    make datetime objects to timezone aware if needed
    """
    if timezone.is_aware(datetime_input):
        return datetime_input

    return timezone.make_aware(
        datetime_input, timezone=use_timezone, is_dst=is_dst)


"""
In [9]: nmap_task=NmapProcess('www.google.com', options='-Pn -p 443 --script ssl-cert')
   ...:

In [10]: nmap_task.run()
Out[10]: 0

In [11]: nmap_task.stdout


In [13]: from libnmap.parser import NmapParser

In [14]: report=NmapParser.parse(nmap_task.stdout)

In [15]: report
Out[15]: NmapReport: started at 1547837399 hosts up 1/1

In [16]: report.summary
Out[16]: 'Nmap done at Fri Jan 18 10:49:59 2019; 1 IP address (1 host up) scanned in 0.67 seconds'

In [17]: report.hosts
Out[17]: [NmapHost: [172.217.0.36 (www.google.com sfo07s26-in-f4.1e100.net) - up]]

In [30]: report.hosts[0].hostnames
Out[30]: ['www.google.com', 'sfo07s26-in-f4.1e100.net']

In [31]: host=report.hosts[0]

In [32]: host.services
Out[32]: [NmapService: [open 443/tcp https ()]]

In [33]: host.services[0]
Out[33]: NmapService: [open 443/tcp https ()]

In [34]: service=host.services[0]

In [35]: service.scripts_results

In [39]: service.get_dict()
Out[39]:
{'id': 'tcp.443',
 'port': '443',
 'protocol': 'tcp',
 'banner': '',
 'service': 'https',
 'state': 'open',
 'reason': 'syn-ack'}


In [43]: service.scripts_results[0]['output'].split('\n')
Out[43]:
['Subject: commonName=www.google.com/organizationName=Google LLC/stateOrProvinceName=California/countryName=US/localityName=Mountain View',
 'Subject Alternative Name: DNS:www.google.com',
 'Issuer: commonName=Google Internet Authority G3/organizationName=Google Trust Services/countryName=US',
 'Public Key type: ec',
 'Public Key bits: 256',
 'Signature Algorithm: sha256WithRSAEncryption',
 'Not valid before: 2018-12-19T08:16:00',
 'Not valid after:  2019-03-13T08:16:00',
 'MD5:   2d45 c59e 4f80 66c5 0900 8cdc 8258 19d8',
 'SHA-1: 3478 1c3b e98c f958 f514 aecb 1ae2 e4e8 66ef fe34',
 '-----BEGIN CERTIFICATE-----',
 'MIIDxzCCAq+gAwIBAgIIDq0DYy9e1dEwDQYJKoZIhvcNAQELBQAwVDELMAkGA1UE',
 'BhMCVVMxHjAcBgNVBAoTFUdvb2dsZSBUcnVzdCBTZXJ2aWNlczElMCMGA1UEAxMc',
 'R29vZ2xlIEludGVybmV0IEF1dGhvcml0eSBHMzAeFw0xODEyMTkwODE2MDBaFw0x',
 'OTAzMTMwODE2MDBaMGgxCzAJBgNVBAYTAlVTMRMwEQYDVQQIDApDYWxpZm9ybmlh',
 'MRYwFAYDVQQHDA1Nb3VudGFpbiBWaWV3MRMwEQYDVQQKDApHb29nbGUgTExDMRcw',
 'FQYDVQQDDA53d3cuZ29vZ2xlLmNvbTBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IA',
 'BEv5RxuoqMukxsAtRd5D87z10pj0JZBvEw14GqwFtN979gZcgJeaUwbQ2w4VrQPe',
 'FAnTd1SxThWor+P93J2t4MWjggFSMIIBTjATBgNVHSUEDDAKBggrBgEFBQcDATAO',
 'BgNVHQ8BAf8EBAMCB4AwGQYDVR0RBBIwEIIOd3d3Lmdvb2dsZS5jb20waAYIKwYB',
 'BQUHAQEEXDBaMC0GCCsGAQUFBzAChiFodHRwOi8vcGtpLmdvb2cvZ3NyMi9HVFNH',
 'SUFHMy5jcnQwKQYIKwYBBQUHMAGGHWh0dHA6Ly9vY3NwLnBraS5nb29nL0dUU0dJ',
 'QUczMB0GA1UdDgQWBBSgt0IIK7d/bpToVbC8gzOp6Fw/qjAMBgNVHRMBAf8EAjAA',
 'MB8GA1UdIwQYMBaAFHfCuFCaZ3Z2sS3ChtCDoH6mfrpLMCEGA1UdIAQaMBgwDAYK',
 'KwYBBAHWeQIFAzAIBgZngQwBAgIwMQYDVR0fBCowKDAmoCSgIoYgaHR0cDovL2Ny',
 'bC5wa2kuZ29vZy9HVFNHSUFHMy5jcmwwDQYJKoZIhvcNAQELBQADggEBAKd6Yiud',
 '9vFUkdoF3UnarCqa+DFK6HBz8PrPGUqxHiueeJPj/Y9MAyNGXhTXtnnhh/Ef+8Pd',
 'zmfwDMJFF+r7+i8TKArGTK7Rl2FSQakTZejHWFFRpsnMrHGpzaABRGIZyGEZQAWs',
 'JZqne6vu4e3g+ExhKbHIX3+W519vt5W0nXTNjM7UPTMqWfimmnRhcVb5IjJAhElo',
 'd7Vt4Tybun81jegIeixvpVwSEX2MVg8v/iPdQtvBuDeKThtNcULWGKJLuD3TYlGN',
 'ZjUcMIaFVTfEkZWL6bm2Ff77l7U9njFKPxToEorAAloJtepmiAVflECWYDAYyh0w',
 'UfuSf04Rd2+/U5o=',
 '-----END CERTIFICATE-----',
 '']

In [44]: service.scripts_results[0]['elements']
Out[44]:
{'subject': {'countryName': 'US',
  'commonName': 'www.google.com',
  'localityName': 'Mountain View',
  'stateOrProvinceName': 'California',
  'organizationName': 'Google LLC'},
 'issuer': {'commonName': 'Google Internet Authority G3',
  'organizationName': 'Google Trust Services',
  'countryName': 'US'},
 'pubkey': {'ecdhparams': '\n', 'bits': '256', 'type': 'ec'},
 'extensions': {None: ['\n', '\n', '\n', '\n', '\n', '\n', '\n', '\n', '\n']},
 'sig_algo': 'sha256WithRSAEncryption',
 'validity': {'notBefore': '2018-12-19T08:16:00',
  'notAfter': '2019-03-13T08:16:00'},
 'md5': '2d45c59e4f8066c509008cdc825819d8',
 'sha1': '34781c3be98cf958f514aecb1ae2e4e866effe34',
 'pem': '-----BEGIN CERTIFICATE-----\nMIIDxzCCAq+gAwIBAgIIDq0DYy9e1dEwDQYJKoZIhvcNAQELBQAwVDELMAkGA1UE\nBhMCVVMxHjAcBgNVBAoTFUdvb2dsZSBUcnVzdCBTZXJ2aWNlczElMCMGA1UEAxMc\nR29vZ2xlIEludGVybmV0IEF1dGhvcml0eSBHMzAeFw0xODEyMTkwODE2MDBaFw0x\nOTAzMTMwODE2MDBaMGgxCzAJBgNVBAYTAlVTMRMwEQYDVQQIDApDYWxpZm9ybmlh\nMRYwFAYDVQQHDA1Nb3VudGFpbiBWaWV3MRMwEQYDVQQKDApHb29nbGUgTExDMRcw\nFQYDVQQDDA53d3cuZ29vZ2xlLmNvbTBZMBMGByqGSM49AgEGCCqGSM49AwEHA0IA\nBEv5RxuoqMukxsAtRd5D87z10pj0JZBvEw14GqwFtN979gZcgJeaUwbQ2w4VrQPe\nFAnTd1SxThWor+P93J2t4MWjggFSMIIBTjATBgNVHSUEDDAKBggrBgEFBQcDATAO\nBgNVHQ8BAf8EBAMCB4AwGQYDVR0RBBIwEIIOd3d3Lmdvb2dsZS5jb20waAYIKwYB\nBQUHAQEEXDBaMC0GCCsGAQUFBzAChiFodHRwOi8vcGtpLmdvb2cvZ3NyMi9HVFNH\nSUFHMy5jcnQwKQYIKwYBBQUHMAGGHWh0dHA6Ly9vY3NwLnBraS5nb29nL0dUU0dJ\nQUczMB0GA1UdDgQWBBSgt0IIK7d/bpToVbC8gzOp6Fw/qjAMBgNVHRMBAf8EAjAA\nMB8GA1UdIwQYMBaAFHfCuFCaZ3Z2sS3ChtCDoH6mfrpLMCEGA1UdIAQaMBgwDAYK\nKwYBBAHWeQIFAzAIBgZngQwBAgIwMQYDVR0fBCowKDAmoCSgIoYgaHR0cDovL2Ny\nbC5wa2kuZ29vZy9HVFNHSUFHMy5jcmwwDQYJKoZIhvcNAQELBQADggEBAKd6Yiud\n9vFUkdoF3UnarCqa+DFK6HBz8PrPGUqxHiueeJPj/Y9MAyNGXhTXtnnhh/Ef+8Pd\nzmfwDMJFF+r7+i8TKArGTK7Rl2FSQakTZejHWFFRpsnMrHGpzaABRGIZyGEZQAWs\nJZqne6vu4e3g+ExhKbHIX3+W519vt5W0nXTNjM7UPTMqWfimmnRhcVb5IjJAhElo\nd7Vt4Tybun81jegIeixvpVwSEX2MVg8v/iPdQtvBuDeKThtNcULWGKJLuD3TYlGN\nZjUcMIaFVTfEkZWL6bm2Ff77l7U9njFKPxToEorAAloJtepmiAVflECWYDAYyh0w\nUfuSf04Rd2+/U5o=\n-----END CERTIFICATE-----\n'}

In [45]:


"""
