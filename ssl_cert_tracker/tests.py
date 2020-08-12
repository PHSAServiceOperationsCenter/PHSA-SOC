"""
ssl_cert_tracker.tests
----------------------

This module contains tests for the :ref:`SSL Certificate Tracker Application`.
:copyright:

    Copyright 2020 - Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from collections import namedtuple

from django.test import TestCase

from ssl_cert_tracker.models import SslCertificateIssuer, SslCertificate


class SslCertificateIssuerTest(TestCase):
    """
    Tests for SSL Certificat Issuer
    """
    def test_getorcreate(self):
        """
        test that get or create returns an issuer.
        """
        self.assertIsInstance(SslCertificateIssuer.get_or_create({}),
                              SslCertificateIssuer)


class SslCertificateTest(TestCase):
    """
    Tests for SSL Certificate
    """
    def test_createorupdate(self):
        """
        Test that create or update does that.
        """
        ssl_data = namedtuple(
            'ssl_data',
            'ssl_issuer, port, ssl_subject, hostnames, ssl_not_before, '
            'ssl_not_after, ssl_pem, ssl_pk_bits, ssl_pk_type, ssl_md5, '
            'ssl_sha1')

        fakes = ['fake']*4

        self.assertTrue(
            SslCertificate.create_or_update(
                ssl_data(
                    {}, 443, {}, 'hosts', '2000-01-01 00:00',
                    '2000-01-01 00:00', 'pem', *fakes), orion_id=3253
            )[0])
