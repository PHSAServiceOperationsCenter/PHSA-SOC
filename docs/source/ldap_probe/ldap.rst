`AD` Services Monitoring Using LDAP
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

* The client can authenticate and connect (`bind`) to the node with the
  specified account credentials and it can execute an extended search
  operation with the specified search configuration (see
  :class:`ldap_probe.models.LDAPBindCred.ldap_base_search`). This
  application is refering to this case as a successful `bind` or `full bind`.
  
  This is the ideal case: the `AD` node is up and providing full services
  
* The client can authenticate and connect to the node with the specified
  account credentials but an extended search operation with the specified
  search configuration raises a `REFFERAL` exception.
  
  This is still a very satisfactory case. We were able to `bind` to the
  `AD` node and the `REFFERAL` exception contains enough information that
  we can try another extended search operation if we so desire. In our
  case we are stating that this outcome is also proof of a functioning
  `AD` network node
  
* The client cannot authenticate and connect to the node with the specified
  account credentials but the client will successfully negotiate an
  `anonymous bind` request with the `AD` node.
