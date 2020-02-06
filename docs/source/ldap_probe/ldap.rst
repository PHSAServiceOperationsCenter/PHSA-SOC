AD Services Monitoring Using LDAP
===================================

The :ref:`Active Directory Services Monitoring Application` has been
developed using `Python` and there is no specialized `Python` package,
module, or library for such services that we are aware of.

We are therefore using the `python-ldap
<https://www.python-ldap.org/en/python-ldap-3.2.0/index.html>`__ package
to communicate with `ADS` nodes using the `LDAP <https://ldap.com/>`__
protocol.

The only caveat when using this module is that cross-domain authentication
and/or searching will sometimes fail. This is not considered an error
by the :ref:`Active Directory Services Monitoring Application`. A failed
`bind` operation can still be proof that the `AD` service node that
rejected the request is up and functional.


.. note::

    In `LDAP` speak a successful connection is refered to as a `bind`.
    When the `bind` command has returned without raising an exception, the
    `LDAP` protocol guarantees that the client has successfully negotiated
    a connection with the `AD` services network node.



This application is considering the following cases when communicating
with an `AD` services network node:

.. _bind_and_search:

* The client can authenticate and connect (`bind`) to the node with the
  specified account credentials and it can execute an `extended search`
  operation with the specified search configuration (see
  :class:`ldap_probe.models.LDAPBindCred.ldap_base_search`). This
  application is refering to this case as a successful `bind` or `full bind`.

  This is the ideal case: the `AD` node is up and providing full services.
  Here is a sample of the reponse an `AD` node will provide to an `extended
  search` command::

    [('CN=LoginPI01,OU=Target,OU=Users,OU=LoginPI,OU=VCH QA,DC=vch,DC=ca',
      {'objectClass': [b'top', b'person', b'organizationalPerson', b'user'],
       'cn': [b'LoginPI01'],
       'sn': [b'LoginPI01'],
       'givenName': [b'LoginPI01'],
       'distinguishedName': [b'CN=LoginPI01,OU=Target,OU=Users,OU=LoginPI,OU=VCH QA,DC=vch,DC=ca'],
       'instanceType': [b'4'],
       'whenCreated': [b'20180421005916.0Z'],
       'whenChanged': [b'20191129105823.0Z'],
       'displayName': [b'LoginPI01'],
       'uSNCreated': [b'2049424'],
       'memberOf': [b'CN=Tableau Analytices_All Users (RL),OU=Level 2,OU=Security Groups,OU=VCH Groups,OU=VCH,DC=vch,DC=ca', b'CN=LoginPI,OU=LoginPI,OU=VCH QA,DC=vch,DC=ca'],
       'uSNChanged': [b'112352332'],
       'wWWHomePage': [b'http://www.loginvsi.com'],
       'name': [b'LoginPI01'],
       'objectGUID': [b'\xb5qc\xf1\xa3\xa3\xefH\xa5\x83\xde>o\xd72h'],
       'userAccountControl': [b'66048'],
       'badPwdCount': [b'0'],
       'codePage': [b'0'],
       'countryCode': [b'0'],
       'badPasswordTime': [b'132192062997619011'],
       'lastLogon': [b'132200622462833366'],
       'scriptPath': [b'PI_Logon.cmd'],
       'pwdLastSet': [b'131687642516940149'],
       'primaryGroupID': [b'513'],
       'userParameters': [b'CtxCfgPresent P\x10\x1a\x08\x01CtxCfgPresent\xe3\x94\xb5\xe6\x94\xb1\xe6\x88\xb0\xe3\x81\xa2 \x02\x01CtxWFProfilePath\xe3\x80\xb0"\x04\x01CtxWFProfilePathW\xe3\x80\xb0\xe3\x80\xb0\x18\x02\x01CtxWFHomeDir\xe3\x80\xb0\x1a\x04\x01CtxWFHomeDirW\xe3\x80\xb0\xe3\x80\xb0"\x02\x01CtxWFHomeDirDrive\xe3\x80\xb0$\x04\x01CtxWFHomeDirDriveW\xe3\x80\xb0\xe3\x80\xb0\x12\x08\x01CtxShadow\xe3\x84\xb0\xe3\x80\xb0\xe3\x80\xb0\xe3\x80\xb0.\x08\x01CtxMaxDisconnectionTime\xe3\x80\xb0\xe3\x80\xb0\xe3\x80\xb0\xe3\x80\xb0(\x08\x01CtxMaxConnectionTime\xe3\x80\xb0\xe3\x80\xb0\xe3\x80\xb0\xe3\x80\xb0\x1c\x08\x01CtxMaxIdleTime\xe3\x80\xb0\xe3\x80\xb0\xe3\x80\xb0\xe3\x80\xb0 \x02\x01CtxWorkDirectory\xe3\x80\xb0"\x04\x01CtxWorkDirectoryW\xe3\x80\xb0\xe3\x80\xb0\x18\x08\x01CtxCfgFlags1\xe3\x80\xb0\xe3\x80\xb1\xe3\x80\xb2\xe3\x80\xb9"\x02\x01CtxInitialProgram\xe3\x80\xb0$\x04\x01CtxInitialProgramW\xe3\x80\xb0\xe3\x80\xb0'],
       'objectSid': [b'\x01\x05\x00\x00\x00\x00\x00\x05\x15\x00\x00\x00\xeb%y,\x07\xe5;+C\x17\n2&e\x02\x00'],
       'accountExpires': [b'9223372036854775807'],
       'logonCount': [b'36313'],
       'sAMAccountName': [b'LoginPI01'],
       'sAMAccountType': [b'805306368'],
       'userPrincipalName': [b'LoginPI01@VCH.CA'],
       'lockoutTime': [b'0'],
       'objectCategory': [b'CN=Person,CN=Schema,CN=Configuration,DC=vrhb,DC=local'],
       'dSCorePropagationData': [b'16010101000000.0Z'],
       'lastLogonTimestamp': [b'132194986836813450']}
     ),
     (None, ['ldaps://DomainDnsZones.vch.ca/DC=DomainDnsZones,DC=vch,DC=ca'])]

* The client can authenticate and connect to the node with the specified
  account credentials but an `extended search` operation with the specified
  search configuration raises a `REFFERAL` exception.

  This is still a very satisfactory case. We were able to `bind` to the
  `AD` node and the `REFFERAL` exception contains enough information that
  we can try another `extended search` operation if we so desire. In our
  case we are stating that this outcome is also proof of a functioning
  `AD` network node.

  Here is a sample of the response the `AD` node will provide to an
  `extended search` command in this case (it is the equivalent of "I can't
  answer your question but ask this person, they may know."::

    REFERRAL: ldaps://vch.ca/dc=vch,dc=ca

.. _anon_bind_and_search:

* The client cannot authenticate and connect to the node with the specified
  account credentials but the client will successfully negotiate an
  `anonymous bind` request with the `AD` node. Once an `anonymous bind` has
  been negotiated, the client can execute a `read root` command.

  This the minimal satisfactory case. The `AD` services network node is
  accepting connections and answering to specific information requests.

  Here is a sample of the response that an `AD` node will provide to a `read
  root DSE` command::

    {'currentTime': [b'20191205233248.0Z'],
     'subschemaSubentry': [b'CN=Aggregate,CN=Schema,CN=Configuration,DC=ehcnet,DC=ca'],
     'dsServiceName': [b'CN=NTDS Settings,CN=SRVCS03,CN=Servers,CN=Broadway,CN=Sites,CN=Configuration,DC=ehcnet,DC=ca'],
     'namingContexts': [b'CN=Configuration,DC=ehcnet,DC=ca',
                        b'CN=Schema,CN=Configuration,DC=ehcnet,DC=ca',
                        b'DC=phsabc,DC=ehcnet,DC=ca',
                        b'DC=ForestDnsZones,DC=ehcnet,DC=ca',
                        b'DC=DomainDnsZones,DC=phsabc,DC=ehcnet,DC=ca'],
     'defaultNamingContext': [b'DC=phsabc,DC=ehcnet,DC=ca'],
     'schemaNamingContext': [b'CN=Schema,CN=Configuration,DC=ehcnet,DC=ca'],
     'configurationNamingContext': [b'CN=Configuration,DC=ehcnet,DC=ca'],
     'rootDomainNamingContext': [b'DC=ehcnet,DC=ca'],
     'supportedControl': [b'1.2.840.113556.1.4.319', b'1.2.840.113556.1.4.801',
                          b'1.2.840.113556.1.4.473', b'1.2.840.113556.1.4.528',
                          b'1.2.840.113556.1.4.417', b'1.2.840.113556.1.4.619',
                          b'1.2.840.113556.1.4.841', b'1.2.840.113556.1.4.529',
                          b'1.2.840.113556.1.4.805', b'1.2.840.113556.1.4.521',
                          b'1.2.840.113556.1.4.970', b'1.2.840.113556.1.4.1338',
                          b'1.2.840.113556.1.4.474', b'1.2.840.113556.1.4.1339',
                          b'1.2.840.113556.1.4.1340', b'1.2.840.113556.1.4.1413',
                          b'2.16.840.1.113730.3.4.9', b'2.16.840.1.113730.3.4.10',
                          b'1.2.840.113556.1.4.1504', b'1.2.840.113556.1.4.1852',
                          b'1.2.840.113556.1.4.802', b'1.2.840.113556.1.4.1907',
                          b'1.2.840.113556.1.4.1948', b'1.2.840.113556.1.4.1974',
                          b'1.2.840.113556.1.4.1341', b'1.2.840.113556.1.4.2026',
                          b'1.2.840.113556.1.4.2064', b'1.2.840.113556.1.4.2065',
                          b'1.2.840.113556.1.4.2066', b'1.2.840.113556.1.4.2090',
                          b'1.2.840.113556.1.4.2205', b'1.2.840.113556.1.4.2204',
                          b'1.2.840.113556.1.4.2206', b'1.2.840.113556.1.4.2211',
                          b'1.2.840.113556.1.4.2239', b'1.2.840.113556.1.4.2255',
                          b'1.2.840.113556.1.4.2256'],
     'supportedLDAPVersion': [b'3', b'2'],
     'supportedLDAPPolicies': [b'MaxPoolThreads', b'MaxPercentDirSyncRequests',
                               b'MaxDatagramRecv', b'MaxReceiveBuffer',
                               b'InitRecvTimeout', b'MaxConnections',
                               b'MaxConnIdleTime', b'MaxPageSize',
                               b'MaxBatchReturnMessages', b'MaxQueryDuration',
                               b'MaxTempTableSize', b'MaxResultSetSize',
                               b'MinResultSets', b'MaxResultSetsPerConn',
                               b'MaxNotificationPerConn', b'MaxValRange',
                               b'MaxValRangeTransitive', b'ThreadMemoryLimit',
                               b'SystemMemoryLimitPercent'],
     'highestCommittedUSN': [b'183407192'],

     'supportedSASLMechanisms': [b'GSSAPI', b'GSS-SPNEGO', b'EXTERNAL', b'DIGEST-MD5'],
     'dnsHostName': [b'srvcs03.phsabc.ehcnet.ca'],
     'ldapServiceName': [b'ehcnet.ca:srvcs03$@PHSABC.EHCNET.CA'],
     'serverName': [b'CN=SRVCS03,CN=Servers,CN=Broadway,CN=Sites,CN=Configuration,DC=ehcnet,DC=ca'],
     'supportedCapabilities': [b'1.2.840.113556.1.4.800', b'1.2.840.113556.1.4.1670',
                               b'1.2.840.113556.1.4.1791', b'1.2.840.113556.1.4.1935',
                               b'1.2.840.113556.1.4.2080', b'1.2.840.113556.1.4.2237'],
     'isSynchronized': [b'TRUE'],
     'isGlobalCatalogReady': [b'TRUE'],
     'domainFunctionality': [b'2'],
     'forestFunctionality': [b'2'],
     'domainControllerFunctionality': [b'6']}

* The client cannot connect to the `AD` node. This is an error case and it may
  happen when:

  * The `AD` node is down

  * The `AD` node is not in `DNS`

  * The `AD` node is not offering service over `ldaps`. `ldaps` is the secure
    version of the `LDAP` protocol

  * The `AD` node is listening for `LDAP` requests on a port other than the
    `ldaps` default port. For reference, the default port for `ldaps` is 636,
    and the default port for `ldap` is 389
