"""
.. _models:

django models for the ssl_certificates app

:module:    test_utils.py

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""
import os
import sys
import re
import logging
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

import xml.dom.minidom
from lxml import etree

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from ssl_cert_tracker.utils import validate, init_record, \
    process_xml_cert, check_tag


class TestSslCertTrackerTestUtils(object):
    """TestSslCertTrackerTestUtils injects different sets of values
       into utils modules and verifies the result
    """

    def setup(self):
        """setUp"""

    def teardown(self):
        """TearDown"""

    @staticmethod
    def test_check_tag_valid():
        """test_check_tag_valid reads a valid xml file
        from data folder and checks the tags"""

        db_cols = ["organization_name",
                   "country_name",
                   "sig_algo",
                   "bits",
                   "not_before",
                   "not_after",
                   "md5",
                   "xml_data",
                   "addresses",
                   "orion_id",
                   "sha1"]
        doc = xml.dom.minidom.parse(
            os.getcwd() + "/ssl_cert_tracker/tests/data/good.xml")
        for host in doc.getElementsByTagName("host"):
            scripts = host.getElementsByTagName("script")
            record = init_record()
            record["xml_data"] = xml.dom.minidom.parse(os.getcwd() +
                                                       "/ssl_cert_tracker/tests/data/good.xml")
            record["addresses"] = "11.12.14.10"
            record["orion_id"] = "67890"
            for script in scripts:
                # Get cert details for each target
                for elem in script.getElementsByTagName("elem"):
                    check_tag(elem, record, "common_name", "commonName")
                    check_tag(elem, record, "organization_name",
                              "organizationName")
                    check_tag(elem, record, "organization_name",
                              "organizationName")
                    check_tag(elem, record, "country_name", "countryName")
                    check_tag(elem, record, "sig_algo", "sig_algo")
                    check_tag(elem, record, "name", "name")
                    check_tag(elem, record, "bits", "bits")
                    check_tag(elem, record, "not_before", "notBefore")
                    check_tag(elem, record, "not_after", "notAfter")
                    check_tag(elem, record, "md5", "md5")
                    check_tag(elem, record, "sha1", "sha1")

            for key in db_cols:
                assert record[key] is not None

    @staticmethod
    def test_xml_data_md5():
        """test_check_xml_data_md5_no_value reads a  xml file
        from data folder that has a missing tag"""

        doc = xml.dom.minidom.parse(
            os.getcwd() + "/ssl_cert_tracker/tests/data/no_md5_tag.xml")
        for host in doc.getElementsByTagName("host"):
            scripts = host.getElementsByTagName("script")
            record = init_record()
            record["xml_data"] = xml.dom.minidom.parse(os.getcwd() +
                                                       "/ssl_cert_tracker/tests/data/no_md5_tag.xml")
            record["addresses"] = "1.210.310.410"
            record["orion_id"] = "43578"
            for script in scripts:
                # Get cert details for each target
                for elem in script.getElementsByTagName("elem"):
                    check_tag(elem, record, "common_name", "commonName")
                    check_tag(elem, record, "organization_name",
                              "organizationName")
                    check_tag(elem, record, "organization_name",
                              "organizationName")
                    check_tag(elem, record, "country_name", "countryName")
                    check_tag(elem, record, "sig_algo", "sig_algo")
                    check_tag(elem, record, "name", "name")
                    check_tag(elem, record, "bits", "bits")
                    check_tag(elem, record, "not_before", "notBefore")
                    check_tag(elem, record, "not_after", "notAfter")
                    check_tag(elem, record, "md5", "md5")
                    check_tag(elem, record, "sha1", "sha1")
            assert record["md5"] is None

    def test_check_xml_Malformed(self):
        """test_check_xml_data_Malformed reads a  xml file
        from data folder that has a mis-matching tag"""

        return_code = self.check_file_type(os.getcwd() +
                                           "/ssl_cert_tracker/tests/data/malformed.xml")
        assert return_code == "Is INVALID"

    @staticmethod
    def check_file_type(file_name):
        """check_file_type readscheck if file is xml type
        """
        with open(file_name, 'r') as file_handle:
            # Remove tabs, spaces, and new lines when reading
            data = re.sub(r'\s+', '', file_handle.read())
            try:
                etree.parse(StringIO(data))
                return 'Is XML'
            except Exception as ex:
                logging.error("Error proceesing xml_file:%s", ex)
                return 'Is INVALID'

    @staticmethod
    def test_validate_true():
        """test_validate_true validates all valid dates"""
        valid_date_items = ["2000-01-15",
                            "2020-08-10T12:00:00+00:00",
                            "2019-05-11T21:08:07+00:00"]

        for item in valid_date_items:
            assert validate(item) is True

    @staticmethod
    def test_validate_false():
        """test_validate_false validates all invalid dates"""
        invalid_date_items = ["011-15-2000",
                              "ABC-01-2000",
                              "1234567-01-15",
                              "2018-02-29T21:08:07+00:00",
                              "",
                              "2019-15-15T21:08:07+00:00"]
        for item in invalid_date_items:
            assert validate(item) is False

    @staticmethod
    def test_init_record():
        """test_init_record checks if instance is a dict"""
        assert isinstance(init_record(), dict)

    @staticmethod
    def test_process_xml_cert():
        """test_process_xml_cert reads a valid xml file
        from data folder and checks the tags"""

        doc = xml.dom.minidom.parse(
            os.getcwd() + "/ssl_cert_tracker/tests/data/good.xml")
        record = process_xml_cert(12345, doc)
        for key in record:
            assert record[key] is not None
