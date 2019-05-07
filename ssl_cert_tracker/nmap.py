"""
.. _nmap:

nmap functions and classes for the ssl_certificates app

:module:    ssl_cert_tracker.nmap

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Jan. 18, 2019

"""
import csv
import logging
import socket

from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from libnmap.process import NmapProcess
from libnmap.parser import NmapParser

LOG = logging.getLogger('ssl_cert_tracker_log')

from .models import SslProbePort


class NmapTargetError(Exception):
    """
    raise when nmap is invoked with no target
    """


class NmapError(Exception):
    """
    raise if the nmap probe returns an error
    """


class NmapHostDownError(Exception):
    """
    raise if nmap reports the host as down
    """


class NmapTooManyHostsError(Exception):
    """
    raise if the nmap probe returns more than one host

    no idea how this can happen but hte data structures suggest that it is
    possible
    """


class NmapNotAnSslNodeError(Exception):
    """
    raise if there is no SSL data returned by the probe
    """


class NmapProbe():
    """
    class for data returned by an nmap probe
    """

    def __init__(self, address=None, opts=None, logger=LOG):
        """
        :arg address: the network name or address of the node

        :arg str opts: the options to be used by nmap

        :arg `logging.logger` logger: the logger

        :raises:

            :exception:`<NmapTargetError>` if the address argument is
            missing


        """
        if address is None:
            raise NmapTargetError('must provide a target for the nmap probe')

        self._address = address

        if opts is None:
            opts = ''
        self._opts = opts
        self._logger = logger

        self.nmap_data = self.probe_node()

    def probe_node(self):
        """
        execute an nmap probe against a network node

        """
        self._logger.debug(
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
        :returns:

            the summary of the :class:`<libnmap.objects.report.NmapReport>`
            instance created by :method:`<libnmap.parser.NmapParser.parse>`
        """
        return self.nmap_data.summary

    @property
    def host(self):
        """
        :returns:

            the :class:`<libnmap.objects.host.NmapHost>` where the SSL
            service is supposed to be running

        :raises:

            :exception:`<NmapHostDownError>`

            :exception:`<NmapTooManyHostsError>`
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
        :returns: the host names returned by the nmap probe
        """
        return self.host.hostnames

    @property
    def service(self):
        """
        :returns: the nmap service data
        """
        return self.host.services[0]

    @property
    def port(self):
        """
        the network port
        """
        return self.service.port

    @property
    def protocol(self):
        """
        the network protocol
        """
        return self.service.protocol

    @property
    def state(self):
        """
        the port state
        """
        return self.service.state

    @property
    def reason(self):
        """
        the reason for the port state
        """
        return self.service.reason


class SslProbe(NmapProbe):
    """
    nmap data for ssl nodes
    """

    def __init__(
            self, address=None, port=settings.SSL_DEFAULT_PORT, logger=LOG):

        opts = r'{}'.format(settings.SSL_PROBE_OPTIONS % port)

        super().__init__(address, opts, logger)

        self.ssl_data = self.get_ssl_data()

    def get_ssl_data(self):
        """
        :returns: the SSL certificate data

        :raises: :exception:`<NmapNotAnSslNodeError>`
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
        :rtype: ``dict``
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
        public key bits
        """
        return self.ssl_data.get('pubkey', None).get('bits', None)

    @property
    def ssl_pk_type(self):
        """
        public key type
        """
        return self.ssl_data.get('pubkey', None).get('type', None)

    @property
    def ssl_pem(self):
        """
        SSL certificate data
        """
        return self.ssl_data.get('pem', None)

    @property
    def ssl_md5(self):
        """
        MD5 sum
        """
        return self.ssl_data.get('md5', None)

    @property
    def ssl_sha1(self):
        """
        SHA-1 sum
        """
        return self.ssl_data.get('sha1', None)

    @property
    def ssl_not_before(self):
        """
        not valid before
        """
        return make_aware(
            parse_datetime(
                self.ssl_data.get('validity', None).get('notBefore', None)
            ))

    @property
    def ssl_not_after(self):
        """
        not valid after
        """
        return make_aware(
            parse_datetime(
                self.ssl_data.get('validity', None).get('notAfter', None)
            ))


def to_hex(input_string=None):
    """
    :returns: the hex representation of the input string
    :rtype: str

    we need this mostly to reduce md5 and sha1 hashes to some fixed length
    output so that we can avoid truncation problems. it also makes database
    idenxing work easier if all the column values have the same length

    :arg str input: the string to hex encode

    :raises: ``TypeError`` if the input cannot be cast to a string
    """
    if input_string is None:
        return None

    try:
        input_string = str(input_string)
    except Exception as error:
        raise TypeError(
            'cannot cast %s to string: %s' % (input_string, error))

    return bytes(input_string, 'utf8').hex()


def make_aware(datetime_input, use_timezone=timezone.utc, is_dst=False):
    """
    make datetime objects to timezone aware if needed
    """
    if timezone.is_aware(datetime_input):
        return datetime_input

    return timezone.make_aware(
        datetime_input, timezone=use_timezone, is_dst=is_dst)


def probe_for_state(dns_list=None):
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
    and a file with nmap errors (may or may not be useful

    """
    field_names = ['dns', 'port', 'common_name', 'not_before', 'expires_on']
    """
    :var field_names: use for the output csv file header row
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
            except Exception as err:
                print(dns, ', ', port, ', ', err)
                dns_errors.append(dict(dns=dns, port=str(port), err=str(err)))

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
    dns_list = []
    with open(csv_file_name) as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            common_name = row['\ufeffCOMMON NAME']
            if not common_name:
                continue
            dns_list.append(common_name.replace(' ', '.'))

    return dns_list
