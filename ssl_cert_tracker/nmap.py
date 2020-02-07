"""
.. _nmap:

NMAP classes and functions
--------------------------

Classes and functions used by the :ref:`SSL Certificate Tracker Application`
to control and monitor `NMAP <https://nmap.org/>`__ scans

This module makes heavy use of the `libnamp
<https://github.com/savon-noir/python-libnmap>`__ package. Documentation for
the `libnmap` package is available at
`<https://libnmap.readthedocs.io/en/latest/index.html>`__.

:module:    ssl_cert_tracker.nmap

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
import csv
import logging
import socket

from dateutil import parser

from django.conf import settings

from libnmap.process import NmapProcess
from libnmap.parser import NmapParser

from p_soc_auto_base import utils

from .models import SslProbePort


LOG = logging.getLogger(__name__)
"""
fall-back logging object for this module

All the functions and methods in this module will use this `Logger` instance
if they are not called with a `logger` argument.
"""


class NmapTargetError(Exception):
    """
    Custom :exc:`Exception` class raised if :meth:`NmapProbe.__init__` is
    invoked without an `address` argument
    """


class NmapError(Exception):
    """
    Custom :exc:`Exception` class raised if the `NMAP <https://nmap.org/>`__
    scan returns an error not handled by other :exc:`Exception` classes in
    this module
    """


class NmapHostDownError(Exception):
    """
    Custom :exc:`Exception` class raised if the `NMAP <https://nmap.org/>`__
    scan reports that the `Target
    <https://nmap.org/book/man-target-specification.html>`__ host is down
    """


class NmapTooManyHostsError(Exception):
    """
    Custom :exc:`Exception` class raised if the `NMAP <https://nmap.org/>`__
    scan returns more than one host

    I have no idea how this can happen but the structure of the
    :class:`libnmap.objects.host.NmapHost` suggest that it is
    possible
    """


class NmapNotAnSslNodeError(Exception):
    """
    Custom :exc:`Exception` class raised if the `NMAP <https://nmap.org/>`__
    `SSL` scan reports that there is no SSL information for the
    `Target <https://nmap.org/book/man-target-specification.html>`__ host
    """


class NmapProbe:
    """
    Base class for `NMAP <https://nmap.org/>`__ scans

    Note that, unlike other base classes, this class can be used on its own.
    """

    def __init__(self, address=None, opts=None):
        """
        :class:`NmapProbe` constructor

        :arg str address: the network names or addresses reference for the
            `Target  <https://nmap.org/book/man-target-specification.html>`__
            of the `NMAP <https://nmap.org/>`__ scan

        :arg str opts: the options to be used by the `NMAP
            <https://nmap.org/>`__ scan

            See `NMAP Options Summary
            <https://nmap.org/book/man-briefoptions.html>`__ if curiosity
            overwhelms you (but remember how the cat died).

        :arg `logging.Logger` logger: the logging object

        :raises: :exc:`NmapTargetError`


        """
        if address is None:
            raise NmapTargetError('must provide a target for the nmap probe')

        self._address = address
        """the `NMAP` scan target"""

        if opts is None:
            opts = ''
        self._opts = opts
        """the options for the `NMAP` scan"""

        self.nmap_data = self.probe_node()
        """
        :class:`libnmap.objects.report.NmapReport` instance with the data
        collected by the `NMAP <https://nmap.org/>`__ scan
        """

    def probe_node(self):
        """
        launch the `NMAP <https://nmap.org/>`__ scan and parse the results

        :returns:  a :class:`libnmap.objects.report.NmapReport` instance
            with the data collected by the `NMAP <https://nmap.org/>`__ scan

            The :class:`libnmap.objects.report.NmapReport` instance is created
            by calling :meth:`libnmap.parser.NmapParser.parse`

        :raises: :exc:`NmapError` if the `NMAP <https://nmap.org/>`__ scan
            returns anything on `stderr`

        """
        LOG.debug(
            'nmap probe with target %s and options %s',
            self._address, self._opts)

        nmap_task = NmapProcess(self._address, options=self._opts)
        nmap_task.run()

        if nmap_task.stderr and 'warning' not in nmap_task.stderr.lower():
            raise NmapError(nmap_task.stderr)

        return NmapParser.parse(nmap_task.stdout)

    @property
    def summary(self):
        """
        :returns: the summary :attr:`libnmap.objects.report.NmapReport.summary`
            attribute
        """
        return self.nmap_data.summary

    @property
    def host(self):
        """
        :returns: the first entry in the hosts
            :attr:`libnmap.objects.report.NmapReport.hosts` attribute

            We are only returning the first entry because we are always
            intializing :attr:`NmapProbe._address` with info for a single node

            .. todo::

                Clean this up. An `NMAP <https://nmap.org/>`__ scan can
                return information for many hosts. It is only for `SSL` scans
                that we want to focus on one node at a time.

        :rtype: :class:`libnmap.objects.host.NmapHost`

        :raises:

            :exc:`NmapHostDownError`

            :exc:`NmapTooManyHostsError`
        """
        if len(self.nmap_data.hosts) > 1:
            raise NmapTooManyHostsError(
                'the nmap probe to node {}s with options {} returned more'
                ' than one hosts'.format(self._address, self._opts))

        if not self.nmap_data.hosts[0].is_up():
            raise NmapHostDownError(
                'according to the nmap probe node {} is down'.
                format(self._address))

        return self.nmap_data.hosts[0]

    @property
    def hostnames(self):
        """
        :returns: the hostnames
            :attr:`libnmap.objects.host.NmapHost.host.hostnames` attribute

            Information returned by an `NMAP <https://nmap.org/>`__ scan for
            a single target can point to multiple hostnames.

            .. todo::

                See :meth:`NmapProbe.host`.
        """
        return self.host.hostnames

    @property
    def service(self):
        """
        :returns: the first entry in the
            :attr:`libnmap.objects.host.NmapHost.services` attribute of
            *property* :meth:`NmapProbe.host`
        :rtype: :class:`libnmap.objects.service.NmapService`

        .. todo::

            The same considerations as the ones from :meth:`NmapProbe.host`
            apply.
        """
        return self.host.services[0]

    @property
    def port(self):
        """
        :returns: the :attr:`network port
            <libnmap.objects.service.NmapService.port>` attribute of *property*
            :meth:`NmapProbe.service`
        :rtype: int
        """
        return self.service.port

    @property
    def protocol(self):
        """
        :returns: the :attr:`network protocol
            <libnmap.objects.service.NmapService.protocol>` attribute of
            *property* :meth:`NmapProbe.service`
        :rtype: str
        """
        return self.service.protocol

    @property
    def state(self):
        """
        :returns: the :attr:`port state
            <libnmap.objects.service.NmapService.state>` attribute of
            *property* :meth:`NmapProbe.service`
        :rtype: str
        """
        return self.service.state

    @property
    def reason(self):
        """
        :returns: the :attr:`reason for the port state
            <libnmap.objects.service.NmapService.reason>` attribute of
            *property* :meth:`NmapProbe.service`
        :rtype: str
        """
        return self.service.reason


class SslProbe(NmapProbe):
    """
    :class:`NmapProbe` child class specialized in `NMAP <https://nmap.org/>`__
    `SSL server certificate
    <https://en.wikipedia.org/wiki/Public_key_certificate#TLS/SSL_server_certificate>`__
    scans

    .. todo::

        Both :attr:`p_soc_auto.settings.SSL_PROBE_OPTIONS` and
        :attr:`p_soc_auto.settings.SSLDEFAULT_PORT` need to be extended with
        `dynamic preferences` and the :meth:`constructor <__init__>` of this
        class needs to use said `dynamic preference` when initializing.

    See :class:`ssl_cert_tracker.models.SslCertificate` for detailed
    descriptions of the properties in this class.
    """

    def __init__(
            self, address=None, port=settings.SSL_DEFAULT_PORT):
        """
        :arg str address: the DNS name or the IP address of the host that
            will be probed for an `SSL server certificate
            <https://en.wikipedia.org/wiki/Public_key_certificate#TLS/SSL_server_certificate>`__

        :arg int port: the network port that will be probed for an `SSL
            server certificate
            <https://en.wikipedia.org/wiki/Public_key_certificate#TLS/SSL_server_certificate>`__
        """
        opts = r'{}'.format(settings.SSL_PROBE_OPTIONS % port)

        super().__init__(address, opts)

        self.ssl_data = self.get_ssl_data()

    def get_ssl_data(self):
        """
        :returns: the SSL certificate data
        :rtype: dict

        :raises: :exc:`NmapNotAnSslNodeError`
        """
        try:
            return self.service.scripts_results[0].get('elements', None)
        except IndexError:
            raise NmapNotAnSslNodeError('node {} is not an SSL node'.
                                        format(self._address))

    @property
    def ssl_subject(self):
        """
        :returns: the SSL certificate subject data
        :rtype: dict
        """
        return self.ssl_data.get('subject', None)

    @property
    def ssl_issuer(self):
        """
        :returns: the SSL certificate issuer information
        :rtype: ``dict``
        """
        return self.ssl_data.get('issuer', None)

    @property
    def ssl_pk_bits(self):
        """
        :returns: the size of the public key in bits
        :rtype: str
        """
        return self.ssl_data.get('pubkey', None).get('bits', None)

    @property
    def ssl_pk_type(self):
        """
        :returns: the public key type
        :rtype: str
        """
        return self.ssl_data.get('pubkey', None).get('type', None)

    @property
    def ssl_pem(self):
        """
        :returns: the `SSL` certificate `PEM representation
            <https://support.ssl.com/Knowledgebase/Article/View/19/0/der-vs-crt-vs-cer-vs-pem-certificates-and-how-to-convert-them>`__
        :rtype: str
        """
        return self.ssl_data.get('pem', None)

    @property
    def ssl_md5(self):
        """
        :returns: the `MD5 hash <https://en.wikipedia.org/wiki/MD5>`__ of the
            `SSl` certificate
        :rtype: str
        """
        return self.ssl_data.get('md5', None)

    @property
    def ssl_sha1(self):
        """
        :returns: the `SHA-1 hash <https://en.wikipedia.org/wiki/SHA-1>`__ of
            the `SSL` certificate
        :rtype: str
        """
        return self.ssl_data.get('sha1', None)

    @property
    def ssl_not_before(self):
        """
        :returns: the `Not Before` value of the `SSL` certificate
        :rtype: datetime.datetime
        """
        return utils.make_aware(
            parser.parse(
                self.ssl_data.get('validity', None).get('notBefore', None)
            ))

    @property
    def ssl_not_after(self):
        """
        :returns: the `Not After` value of the `SSL` certificate
        :rtype: datetime.datetime
        """
        return utils.make_aware(
            parser.parse(
                self.ssl_data.get('validity', None).get('notAfter', None)
            ))


def to_hex(input_string=None):
    """
    :returns: the hex representation of the input string
    :rtype: str

    We need this mostly to reduce md5 and sha1 hashes to some fixed length
    output so that we can avoid truncation problems. It also makes database
    indexing work easier if all the column values have the same length

    :arg str input: the string to hex encode

    :raises: :exc:`TypeError` if the input cannot be cast to a string
    """
    if input_string is None:
        return None

    input_string = str(input_string)

    return bytes(input_string, 'utf8').hex()


def probe_for_state(dns_list=None):
    """
    try to connect to each DNS name in a list and save the results in
    separate `CSV` files: one file for unresolved hosts, one file for hosts
    known to the `DNS` servers that are not connectable, and one file
    with connectable hosts

    :arg list dns_list: the :class:`list` of DNS names
    """
    if dns_list is None:
        dns_list = []
        with open('no_certs/no_certs.csv') as csv_file:
            reader = csv.DictReader(csv_file)
            for row in reader:
                common_name = row['dns']
                if not common_name:
                    continue
                dns_list.append(common_name)

    hosts_up = []
    hosts_down = []
    hosts_unresolved = []
    for dns in dns_list:
        try:
            socket.gethostbyname(dns)
        except:
            hosts_unresolved.append(dict(dns=dns))
            print('unresolved host: ', dns)
            continue

        try:
            probe = NmapProbe(address=dns, opts='-A -T4 -Pn')
            hosts_up.append(dict(
                dns=dns,
                open_ports=', '.join(
                    [str(service.port) for service in probe.host.services])))
            print(dns, 'open ports: ', ', '.join(
                [str(service.port) for service in probe.host.services]))

        except Exception as err:
            hosts_down.append(dict(dns=dns, err=str(err)))
            print('!!!', dns, str(err))

    write_csv('unresolved.csv', hosts_unresolved, ['dns'])
    write_csv('hosts_open_ports.csv', hosts_up, ['dns', 'open_ports'])
    write_csv('hosts_down.csv', hosts_down, ['dns', 'err'])


def write_csv(file_name, source, fieldnames):
    with open(file_name, 'w', newline='') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

        csv_writer.writeheader()

        for item in source:
            csv_writer.writerow(item)


def probe_for_certs(dns_list=None, port_list=None):
    """
    prepare a file with common name, port, expiration date;
    and a file with the dns list where no certs were found on any of the probed
    ports;
    and a file with nmap errors (may or may not be useful)

    """
    field_names = ['dns', 'port', 'common_name', 'not_before', 'expires_on']
    """
    header row for the csv file
    """

    if dns_list is None:
        dns_list = get_dns_list('certs.csv')

    if port_list is None:
        port_list = list(SslProbePort.objects.values_list('port', flat=True))

    err_field_names = ['dns', 'port', 'err']

    certs = []
    dns_errors = []

    # assume that no dns has any certificates on the listed ports
    dns_no_certs = dns_list

    for dns in dns_list:
        for port in port_list:
            try:

                cert = SslProbe(dns, port)

                # oh, look.... this dns serves a certificate
                # take it out from the list of no certs found
                dns_no_certs.remove(dns)
                certs.append(dict(
                    dns=dns, port=str(port),
                    common_name=cert.ssl_subject.get('commonName'),
                    not_before=cert.ssl_not_before,
                    expires_on=cert.ssl_not_after))
                print('found', cert.ssl_subject.get(
                    'commonName'), ': ', str(port), ', ', cert.ssl_not_after)
            except Exception as error:
                print(f'{dns}, {port}, {error}')
                dns_errors.append(dict(dns=dns, port=str(port), err=str(error)))

    with open('certs_found.csv', 'w', newline='') as csv_file:
        csv_writer = csv.DictWriter(csv_file, fieldnames=field_names)

        csv_writer.writeheader()

        for cert in certs:
            csv_writer.writerow(cert)

    with open('no_certs.csv', 'w', newline='') as no_certs_csv_file:
        fieldnames = ['dns', 'ports']
        no_certs_csv_writer = csv.DictWriter(
            no_certs_csv_file, fieldnames=fieldnames)

        _port_list = [str(port) for port in port_list]
        no_certs_csv_writer.writeheader()
        for dns in dns_no_certs:
            no_certs_csv_writer.writerow(
                {'dns': dns, 'ports': ' '.join(_port_list)})

    with open('dns_cert_errors.csv', 'w', newline='') as err_file:
        err_writer = csv.DictWriter(err_file, fieldnames=err_field_names)

        err_writer.writeheader()
        for dns_error in dns_errors:
            err_writer.writerow(dns_error)


def get_dns_list(csv_file_name):
    """
    get the list DNS names from a comma-separated file exported from
    `Microsoft Excel <https://en.wikipedia.org/wiki/Microsoft_Excel>`__

    Note that this is a very specialized function that depends on having the
    name of the column for DNS names in `UTF-8` format. That column name is
    possibly specific, not only to `Excel`, but also to the particular file
    used for extracting the informantion

    :arg str csv_file_name:

    :returns: a :class:`list` of :class:`strings <str>` with each item
        representing a DNS name
    """
    dns_list = []
    with open(csv_file_name) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            common_name = row['\ufeffCOMMON NAME']
            if not common_name:
                continue
            dns_list.append(common_name.replace(' ', '.'))

    return dns_list
