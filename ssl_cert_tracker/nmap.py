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
import logging

from django.conf import settings
from django.utils.dateparse import parse_datetime
from django.utils import timezone

from libnmap.process import NmapProcess
from libnmap.parser import NmapParser

LOG = logging.getLogger('ssl_cert_tracker_log')


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
