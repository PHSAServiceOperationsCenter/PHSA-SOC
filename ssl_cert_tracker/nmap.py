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

from libnmap.process import NmapProcess
from libnmap.parser import NmapParser

LOG = logging.getLogger('ssl_cert_tracker_log')
SSL_PROBE_OPTIONS = r'-Pn -p 443 --script ssl-cert'


class NmapTargetError(Exception):
    """
    raise when nmap is invoked with no target
    """
    pass


class NmapError(Exception):
    """
    raise if the nmap probe returns an error
    """
    pass


class NmapProbe():
    """
    class for data reeturned by an nmap probe
    """

    def __init__(self, address=None, opts=SSL_PROBE_OPTIONS, logger=LOG):
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
        return self.nmap_data.summary

    @property
    def host(self):
        return self.nmap_data.hosts[0]

    @property
    def service(self):
        return self.host.services[0]

    @property
    def ssl_data(self):
        return self.service.scripts_results[0].get('elements', None)

    @property
    def ssl_subject(self):
        return self.ssl_data.get('subject', None)
