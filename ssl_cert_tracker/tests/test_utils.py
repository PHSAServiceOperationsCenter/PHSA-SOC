"""
.. _models:

django models for the ssl_certificates app

:module:    test_utils.py

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""
import xml.dom.minidom
from django.test import TestCase
from ssl_cert_tracker.utils import validate, init_record, check_tag

class SslCertTrackerTestUtils(TestCase):
    """Ssl_Cert_Tracker_Test_Utils"""
    @classmethod
    def setUpTestData(cls):
        """setUpTestData"""
        cls.valid_date_items = []
        cls.invalid_date_items = []
        cls.xml_data = ""
        cls.db_cols = []
        cls.xml_tags = []
        cls.check_tag_param = ()

    def setUp(self):
        """setUp"""
        self.valid_date_items = ["2000-01-15", \
                                "1998-07-15", \
                                "1999-10-25"]

        self.invalid_date_items = ["011-15-2000", \
                                  "ABC-01-2000", \
                                  "-01-15", \
                                  "2018-02-29", \
                                  "", \
                                  "98-01-15"]

        self.xml_data = """<?xml version="1.0" encoding="UTF-8"?>
        <!DOCTYPE nmaprun>
        <?xml-stylesheet href="file:///C:/Program Files (x86)/Nmap/nmap.xsl" type="text/xsl"?>
        <!-- Nmap 7.70 scan initiated Mon Jul 23 15:23:11 2018 as: &quot;C:\\Program Files (x86)\\Nmap\\nmap.exe&quot; -oX - -vv
        v -p 443,8443 -&#45;stats-every 1s -&#45;script ssl-cert www.yahoo.com www.paypal.com -->
        <nmaprun scanner="nmap" args="&quot;C:\\Program Files (x86)\\Nmap\\nmap.exe&quot; -oX - -vvv -p 443,8443 -&#45;stats-eve
        ry 1s -&#45;script ssl-cert www.yahoo.com www.paypal.com" start="1532384591" startstr="Mon Jul 23 15:23:11 2018" version
        ="7.70" xmloutputversion="1.04">
        <scaninfo type="syn" protocol="tcp" numservices="2" services="443,8443"/>
        <verbose level="3"/>
        <debugging level="0"/>
        <taskbegin task="NSE" time="1532384592"/>
        <taskend task="NSE" time="1532384592"/>
        Warning: Hostname www.yahoo.com resolves to 4 IPs. Using 98.137.246.8.
        <taskbegin task="Ping Scan" time="1532384592"/>
        <taskprogress task="Ping Scan" time="1532384593" percent="6.25" remaining="16" etc="1532384608"/>
        <taskend task="Ping Scan" time="1532384593" extrainfo="2 total hosts"/>
        <taskbegin task="Parallel DNS resolution of 2 hosts." time="1532384595"/>
        <taskend task="Parallel DNS resolution of 2 hosts." time="1532384595"/>
        <taskbegin task="SYN Stealth Scan" time="1532384595"/>
        <taskprogress task="SYN Stealth Scan" time="1532384595" percent="75.00" remaining="1" etc="1532384595"/>
        <taskprogress task="SYN Stealth Scan" time="1532384596" percent="75.00" remaining="1" etc="1532384596"/>
        <taskend task="SYN Stealth Scan" time="1532384596" extrainfo="4 total ports"/>
        <taskbegin task="NSE" time="1532384596"/>
        <taskend task="NSE" time="1532384597"/>
        <host starttime="1532384592" endtime="1532384596"><status state="up" reason="reset" reason_ttl="252"/>
        <address addr="98.137.246.8" addrtype="ipv4"/>
        <hostnames>
        <hostname name="www.yahoo.com" type="user"/>
        <hostname name="media-router-fp2.prod1.media.vip.gq1.yahoo.com" type="PTR"/>
        </hostnames>
        <ports>
        <port protocol="tcp" portid="443">
        <state state="open" reason="syn-ack" reason_ttl="115"/>
        <service name="https" method="table" conf="3"/>
        <script id="ssl-cert" 
        output="Subject: commonName=*.www.yahoo.com/organizationName=Yahoo Holdings
        , Inc./stateOrProvinceName=CA/countryName=US/localityName=Sunnyvale&#xa;Subject Alternative Name: DNS:*.www.yahoo.com, D
        NS:add.my.yahoo.com, DNS:*.amp.yimg.com, DNS:au.yahoo.com, DNS:be.yahoo.com, DNS:br.yahoo.com, DNS:ca.my.yahoo.com, DNS:
        ca.rogers.yahoo.com, DNS:ca.yahoo.com, DNS:ddl.fp.yahoo.com, DNS:de.yahoo.com, DNS:en-maktoob.yahoo.com, DNS:espanol.yah
        88 6d93 a03d 934a e691 1787 48b7&#xa;SHA-1: ae69 9d5e bddc e6ed 5741 1126 2f19 bb18 efbe 73b0&#xa;-&#45;&#45;&#45;&#45;B
        EGIN CERTIFICATE-&#45;&#45;&#45;&#45;&#xa;MIIJAzCCB+ugAwIBAgIQDaKa2VJMH0/z+3Y7vlKxrDANBgkqhkiG9w0BAQsFADBw&#xa;MQswCQYDV
        QnNQ==&#xa;-&#45;&#45;&#45;&#45;END CERTIFICATE-&#45;&#45;&#45;&#45;&#xa;"><table key="subject">
        <elem key="countryName">US</elem>
        <elem key="organizationName">Yahoo Holdings, Inc.</elem>
        <elem key="localityName">Sunnyvale</elem>
        <elem key="stateOrProvinceName">CA</elem>
        <elem key="commonName">*.www.yahoo.com</elem>
        </table>
        <table key="issuer">
        <elem key="countryName">US</elem>
        <elem key="organizationName">DigiCert Inc</elem>
        <elem key="organizationalUnitName">www.digicert.com</elem>
        <elem key="commonName">DigiCert SHA2 High Assurance Server CA</elem>
        </table>
        <table key="pubkey">
        <elem key="modulus">userdata: 03E88280</elem>
        <elem key="exponent">userdata: 03E88500</elem>
        <elem key="type">rsa</elem>
        <elem key="bits">2048</elem>
        </table>
        <table key="extensions">
        <table>
        <elem key="name">X509v3 Authority Key Identifier</elem>
        <elem key="value">keyid:51:68:FF:90:AF:02:07:75:3C:CC:D9:65:64:62:A2:12:B8:59:72:3B&#xa;</elem>
        </table>
        <table>
        <elem key="name">X509v3 Subject Key Identifier</elem>
        <elem key="value">1C:ED:E7:87:8C:51:60:6E:35:B2:ED:B6:4F:98:6A:16:7F:78:D2:34</elem>
        </table>
        <table>
        <elem key="name">X509v3 Subject Alternative Name</elem>
        <elem key="value">DNS:*.www.yahoo.com, DNS:add.my.yahoo.com, DNS:*.amp.yimg.com, DNS:au.yahoo.com, DNS:be.yahoo.com, DNS
        :br.yahoo.com, DNS:ca.my.yahoo.com, DNS:ca.rogers.yahoo.com, DNS:ca.yahoo.com, DNS:ddl.fp.yahoo.com, DNS:de.yahoo.com, D
        NS:en-maktoob.yahoo.com, DNS:espanol.yahoo.com, DNS:es.yahoo.com, DNS:fr-be.yahoo.com, DNS:fr-ca.rogers.yahoo.com, DNS:f
        rontier.yahoo.com, DNS:fr.yahoo.com, DNS:gr.yahoo.com, DNS:hk.yahoo.com, DNS:hsrd.yahoo.com, DNS:ideanetsetter.yahoo.com
        , DNS:id.yahoo.com, DNS:ie.yahoo.com, DNS:in.yahoo.com, DNS:it.yahoo.com, DNS:maktoob.yahoo.com, DNS:malaysia.yahoo.com,
        DNS:mbp.yimg.com, DNS:my.yahoo.com, DNS:nz.yahoo.com, DNS:ph.yahoo.com, DNS:qc.yahoo.com, DNS:ro.yahoo.com, DNS:se.yaho
        o.com, DNS:sg.yahoo.com, DNS:tw.yahoo.com, DNS:uk.yahoo.com, DNS:us.yahoo.com, DNS:verizon.yahoo.com, DNS:vn.yahoo.com,
        DNS:www.yahoo.com, DNS:yahoo.com, DNS:za.yahoo.com</elem>
        </table>
        <table>
        <elem key="name">X509v3 Key Usage</elem>
        <elem key="critical">true</elem>
        <elem key="value">Digital Signature, Key Encipherment</elem>
        </table>
        <table>
        <elem key="name">X509v3 Extended Key Usage</elem>
        <elem key="value">TLS Web Server Authentication, TLS Web Client Authentication</elem>
        </table>
        <table>
        <elem key="name">X509v3 CRL Distribution Points</elem>
        <elem key="value">&#xa;Full Name:&#xa;  URI:http://crl3.digicert.com/sha2-ha-server-g6.crl&#xa;&#xa;Full Name:&#xa;  URI
        :http://crl4.digicert.com/sha2-ha-server-g6.crl&#xa;</elem>
        </table>
        <table>
        <elem key="name">X509v3 Certificate Policies</elem>
        <elem key="value">Policy: 2.16.840.1.114412.1.1&#xa;  
        CPS: https://www.digicert.com/CPS&#xa;Policy: 2.23.140.1.2.2&#xa;</elem>
        </table>
        <table>
        <elem key="name">Authority Information Access</elem>
        <elem key="value">OCSP - URI:http://ocsp.digicert.com&#xa;CA Issuers - URI:http://cacerts.digicert.com/DigiCertSHA2HighA
        ssuranceServerCA.crt&#xa;</elem>
        </table>
        <table>
        <elem key="name">X509v3 Basic Constraints</elem>
        <elem key="critical">true</elem>
        <elem key="value">CA:FALSE</elem>
        </table>
        <table>
        <elem key="name">CT Precertificate SCTs</elem>
        <elem key="value">Signed Certificate Timestamp:&#xa;    Version   : v1(0)&#xa;    Log ID    : BB:D9:DF:BC:1F:8A:71:B5:93
        F2:59:1D:B4:56:2E:7E:0F:&#xa;                FE:54:7D:48:80:E6:99:B1</elem>
        </table>
        </table>
        <elem key="sig_algo">sha256WithRSAEncryption</elem>
        <table key="validity">
        <elem key="notBefore">2018-02-26T00:00:00</elem>
        <elem key="notAfter">2018-08-25T12:00:00</elem>
        </table>
        <elem key="md5">57adc7886d93a03d934ae691178748b7</elem>
        <elem key="sha1">ae699d5ebddce6ed574111262f19bb18efbe73b0</elem>
        <elem key="pem">-&#45;&#45;&#45;&#45;BEGIN CERTIFICATE-&#45;&#45;&#45;&#45;&#xa;MIIJAzCCB+ugAwIBAgIQDaKa2VJMH0/z+3Y7vlKx
        rDANBgkqhkiG9w0BAQsFADBw&#xa;MQswCQYDVQQGEwJVUzEVMBMGA1UEChMMRGlnaUNlcnQgSW5jMRkwFwYDVQQLExB3&#xa;d3cuZGlnaWNlcnQuY29tMS
        8wLQYDVQQDEyZEaWdpQ2VydCBTSEEyIEhpZ2ggQXNz&#xa;dXJhbmNlIFNlcnZlciBDQTAeFw0xODAyMjYwMDAwMDBaFw0xODA4MjUxMjAwMDBa&#xa;MGcx
        ngQwBAgIwgYMGCCsGAQUF&#xa;BwEBBHcwdTAkBggrBgEFBQcwAYYYaHR0cDovL29jc3AuZGlnaWNlcnQuY29tME0G&#xa;CCsGAQUFBzAChkFodHRwOi8vY
        2FjZXJ0cy5kaWdpY2VydC5jb20vRGlnaUNlcnRT&#xa;SEEySGlnaEFzc3VyYW5jZVNlcnZlckNBLmNydDAMBgNVHRMBAf8EAjAAMIIBBQYK&#xa;KwYBBAH
        WeQIEAgSB9gSB8wDxAHYAu9nfvB+KcbWTlCOXqpJ7RzhXlQqrUugakJZk&#xa;No4e0YUAAAFh02HjzAAABAMARzBFAiEA3sr1uZcc9b+IzY6z66Rz1yHX1Z
        uVYpnQ&#xa;yTx6WEdb2pgCIGhfjRPibuJ9J3nar8U4qS3FeoXI6sElxrQfi3ct8w3OAHcAh3W/&#xa;51l8+IxDmV+9827/Vo1HVjb/SrVgwbTq/16ggw8A
        AAFh02HjvgAABAMASDBGAiEA&#xa;756cn+DnfAhzgbonXNiHvJtU+SCTho8u23bM14Nh0+MCIQC90B9AckWD5+1o91i9&#xa;ONLt8lkdtFYufg/+VH1IgO
        aZsTANBgkqhkiG9w0BAQsFAAOCAQEATdztspRySWON&#xa;MwcDmLUjKdVq3LIwCQxbQfLzUQHBqmrP9kqSnPDVZn/ALDnjdRGQ4tzGkQlRfGYl&#xa;pry0
        ZfcDwswq6FOR2gqHI/Q+k3FB6PigUlbSVEuARg+VKYFu+B9arQrg4acqUmtf&#xa;fIAh5iVGmWfphg2nPKjpubOfeI/XiknvJG2aEfoLIfR+CHrJ3sN4U2K
        YdBMhusJg&#xa;kY7rprI1r5dNR1IdRgxO4dY+QU4cUsyeGNhRkt4TEeEsDV8UNWQ3ge1qdrwzUHew&#xa;iRrBjlru4U3ziEMzn4V/uUho88WYXOhyVavP0
        8Kqp1XVr/YnzcWL8abPO3mc/nOE&#xa;emkJ4OQnNQ==&#xa;-&#45;&#45;&#45;&#45;END CERTIFICATE-&#45;&#45;&#45;&#45;&#xa;</elem>
        </script></port>
        <port protocol="tcp" portid="8443"><state state="filtered" reason="no-response" reason_ttl="0"/>
        <service name="https-alt" method="table" conf="3"/></port>
        </ports>
        <times srtt="15125" rttvar="11500" to="100000"/>
        </host>
        <host starttime="1532384592" endtime="1532384597"><status state="up" reason="reset" reason_ttl="252"/>
        <address addr="104.100.74.76" addrtype="ipv4"/>
        <hostnames>
        <hostname name="www.paypal.com" type="user"/>
        <hostname name="a104-100-74-76.deploy.static.akamaitechnologies.com" type="PTR"/>
        </hostnames>
        <ports><port protocol="tcp" portid="443">
        <state state="open" reason="syn-ack" reason_ttl="47"/><service name="https" method="table" conf="3"/>
        <script id="ssl-cert" 
        output="Subject: commonName=www.paypal.com/organizationName=PayPal, Inc./sta
        teOrProvinceName=California/countryName=US/serialNumber=3014267/organizationalUnitName=CDN Support/streetAddress=2211 N
        FVnBWhlIjnjfjbZkNI9BjbH3u701t3aw/us&#xa;Q/4vHGSb4t3AiYtSmI0O9gkt5E1inBYilvtoW5SHh84YfkFgeaQXPnHysaIG2HHY&#xa;Mwtq1GdoJD6
        6xiGUXWr2IYRf0P+s5D2qrZWF/EtpMHK3uk3aOu3ZfUAdAim41QwJ&#xa;ng10i/piAkqIbnwTVrqZPxN4SIKsQ45h&#xa;-&#45;&#45;&#45;&#45;END
        CERTIFICATE-&#45;&#45;&#45;&#45;&#xa;"><table key="subject">
        <elem key="serialNumber">3014267</elem>
        <elem key="commonName">www.paypal.com</elem>
        <elem key="jurisdictionCountryName">US</elem>
        <elem key="organizationalUnitName">CDN Support</elem>
        <elem key="jurisdictionStateOrProvinceName">Delaware</elem>
        <elem key="localityName">San Jose</elem>
        <elem key="countryName">US</elem>
        <elem key="postalCode">95131-2021</elem>
        <elem key="businessCategory">Private Organization</elem>
        <elem key="organizationName">PayPal, Inc.</elem>
        <elem key="streetAddress">2211 N 1st St</elem>
        <elem key="stateOrProvinceName">California</elem>
        </table>
        <table key="issuer">
        <elem key="countryName">US</elem>
        <elem key="organizationName">Symantec Corporation</elem>
        <elem key="organizationalUnitName">Symantec Trust Network</elem>
        <elem key="commonName">Symantec Class 3 EV SSL CA - G3</elem>
        </table>
        <table key="pubkey">
        <elem key="modulus">userdata: 03E88AF0</elem>
        <elem key="exponent">userdata: 03E88CD0</elem>
        <elem key="type">rsa</elem>
        <elem key="bits">2048</elem>
        </table>
        <table key="extensions">
        <table>
        <elem key="name">X509v3 Subject Alternative Name</elem>
        <elem key="value">DNS:history.paypal.com, DNS:t.paypal.com, DNS:c.paypal.com, DNS:c6.paypal.com, DNS:developer.paypal.co
        m, DNS:p.paypal.com, DNS:www.paypal.com</elem>
        </table>
        <table>
        <elem key="name">X509v3 Basic Constraints</elem>
        <elem key="value">CA:FALSE</elem>
        </table>
        <table>
        <elem key="name">X509v3 Key Usage</elem>
        <elem key="critical">true</elem>
        <elem key="value">Digital Signature, Key Encipherment</elem>
        </table>
        <table>
        <elem key="name">X509v3 Extended Key Usage</elem>
        <elem key="value">TLS Web Server Authentication, TLS Web Client Authentication</elem>
        </table>
        <table>
        <elem key="name">X509v3 Certificate Policies</elem>
        <elem key="value">Policy: 2.16.840.1.113733.1.7.23.6&#xa;  CPS: https://d.symcb.com/cps&#xa;  User Notice:&#xa;    Expli
        cit Text: https://d.symcb.com/rpa&#xa;Policy: 2.23.140.1.1&#xa;</elem>
        </table>
        <table>
        <elem key="name">X509v3 Authority Key Identifier</elem>
        <elem key="value">keyid:01:59:AB:E7:DD:3A:0B:59:A6:64:63:D6:CF:20:07:57:D5:91:E7:6A&#xa;</elem>
        </table>
        <table>
        <elem key="name">X509v3 CRL Distribution Points</elem>
        <elem key="value">&#xa;Full Name:&#xa;  URI:http://sr.symcb.com/sr.crl&#xa;</elem>
        </table>
        <table>
        <elem key="name">Authority Information Access</elem>
        <elem key="value">OCSP - URI:http://sr.symcd.com&#xa;CA Issuers - URI:http://sr.symcb.com/sr.crt&#xa;</elem>
        </table>
        <table>
        <elem key="name">CT Precertificate SCTs</elem>
        <elem key="value">Signed Certificate Timestamp:&#xa;    Version   : v1(0)&#xa;    Log ID    : DD:EB:1D:2B:7A:0D:4F:A6:20
        27:98:19:DE:4F:FC:69:0A:22:64:97:70:92:67:9C:7C:&#xa;                F4:00:D1:DF:C2:61:E6</elem>
        </table>
        </table>
        <elem key="sig_algo">sha256WithRSAEncryption</elem>
        <table key="validity">
        <elem key="notBefore">2017-09-22T00:00:00</elem>
        <elem key="notAfter">2019-10-30T23:59:59</elem>
        </table>
        <elem key="md5">cfce8a0f2e0787ab22bf977fcb9828aa</elem>
        <elem key="sha1">bb20b03ffb93e177ff23a7438949601a41aec61c</elem>
        <elem key="pem">-&#45;&#45;&#45;&#45;BEGIN CERTIFICATE-&#45;&#45;&#45;&#45;&#xa;MIIHZDCCBkygAwIBAgIQV8t+FeLj4kTYKwFjKUbr
        8DANBgkqhkiG9w0BAQsFADB3&#xa;MQswCQYDVQQGEwJVUzEdMBsGA1UEChMUU3ltYW50ZWMgQ29ycG9yYXRpb24xHzAd&#xa;BgNVBAsTFlN5bWFudGVjIF
        RydXN0IE5ldHdvcmsxKDAmBgNVBAMTH1N5bWFudGVj&#xa;IENsYXNzIDMgRVYgU1NMIENBIC0gRzMwHhcNMTcwOTIyMDAwMDAwWhcNMTkxMDMw&#xa;MjM1
        b4t3AiYtSmI0O9gkt5E1inBYilvtoW5SHh84YfkFgeaQXPnHysaIG2HHY&#xa;Mwtq1GdoJD66xiGUXWr2IYRf0P+s5D2qrZWF/EtpMHK3uk3aOu3ZfUAdAi
        m41QwJ&#xa;ng10i/piAkqIbnwTVrqZPxN4SIKsQ45h&#xa;-&#45;&#45;&#45;&#45;END CERTIFICATE-&#45;&#45;&#45;&#45;&#xa;</elem>
        </script></port>
        <port protocol="tcp" portid="8443">
        <state state="filtered" reason="no-response" reason_ttl="0"/><service name="https-alt" method="table" conf="3"/></port>
        </ports>
        <times srtt="17000" rttvar="15250" to="100000"/>
        </host>
        <taskbegin task="NSE" time="1532384597"/>
        <taskend task="NSE" time="1532384597"/>
        <runstats><finished time="1532384597" timestr="Mon Jul 23 15:23:17 2018" elapsed="5.82" summary="Nmap done at Mon Jul 23
        15:23:17 2018; 2 IP addresses (2 hosts up) scanned in 5.82 seconds" exit="success"/><hosts up="2" down="0" total="2"/>
        </runstats>
        </nmaprun>"""

        self.db_cols = ["organization_name", \
                         "country_name", \
                         "sig_algo", \
                         "bits", \
                         "not_before", \
                         "not_after", \
                         "md5", \
                         "sha1"]
        self.xml_tags = ["organizationName", \
                         "countryName", \
                         "sig_algo", \
                         "bits", \
                         "notBefore", \
                         "notAfter", \
                         "md5", \
                         "sha1"]
        self.check_tag_param = zip(self.db_cols, self.xml_tags)

    def TearDown(self):
        """TearDown"""
        self.valid_date_items = None
        self.invalid_date_items = None
        self.xml_data = None
        self.db_cols = None
        self.xml_tags = None
        self.check_tag_param = None
        self.xml_data = None

    def test_validate_true(self):
        """test_validate_true"""
        for item in self.valid_date_items:
            self.assertTrue(validate(item))

    def test_validate_false(self):
        """test_validate_false"""
        for item in self.invalid_date_items:
            self.assertFalse(validate(item))

    def test_init_record(self):
        """test_init_record"""
        self.assertIsInstance(init_record(), dict)

    def test_check_tag(self):
        """test_check_tag"""
        doc = xml.dom.minidom.parseString(self.xml_data)
        for host in doc.getElementsByTagName("host"):
            scripts = host.getElementsByTagName("script")
            record = init_record()
            for script in scripts:
                for elem in script.getElementsByTagName("elem"):
                    for item in self.check_tag_param:
                        check_tag(elem, record, item[0], item[1])
            for item in self.check_tag_param:
                self.assertIsNotNone(record[item[0]])
