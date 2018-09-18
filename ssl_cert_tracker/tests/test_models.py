"""
.. _models:

django models for the ssl_certificates app

:module:    test_models.py

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca
"""
from datetime import datetime

from django.test import TestCase
from ssl_cert_tracker.models import NmapCertsData, NmapHistory

class TestSslCertTrackerModels(TestCase):
    """TestSslCertTrackerModels injects different sets of values
       into model fields and verifies the result
    """
    @classmethod
    def setUpTestData(cls):
        """setUpTestData: Initializes all objects/attributes"""
        cls.vNot_Before = None
        cls.vNot_After = None
        cls.obj = None

    def setUp(self):
        """setUp test data"""
        NmapCertsData.created_by = NmapCertsData.get_or_create_user(username='PHSA_User')
        NmapCertsData.objects.create(orion_id='12345',
                                     addresses='10.10.10.10',
                                     not_before=datetime(2018, 1, 21, 14, 32, 24, 38),
                                     not_after=datetime(2018, 11, 21, 19, 30, 45, 21),
                                     xml_data='',
                                     common_name='A Common Name',
                                     organization_name='A Great IT Place',
                                     country_name='Canada',
                                     sig_algo='sha256WithRSAEncryption',
                                     bits='2048',
                                     md5='57adc7886d93a03d934ae691178748b7',
                                     sha1='ae699d5ebddce6ed574111262f19bb18efbe73b0',
                                     created_by_id=NmapCertsData.created_by.id,
                                     updated_by_id=NmapCertsData.created_by.id
                                     )

        self.obj = NmapCertsData.objects.get(orion_id='12345')

    def TearDown(self):
        """Release memory addresses"""

    def test_not_before_content_type(self):
        """testing not_before field"""
        expected_object_not_before = self.obj.not_before
        self.assertIsInstance(expected_object_not_before, datetime)
        self.assertEqual(str(expected_object_not_before), "2018-01-21 14:32:24+00:00")

    def test_not_after_content_type(self):
        """testing not_after field"""
        expected_object_not_after = self.obj.not_after
        self.assertIsInstance(expected_object_not_after, datetime)
        self.assertEqual(str(expected_object_not_after), "2018-11-21 19:30:45+00:00")

    def test_orion_id_content(self):
        """testing orion field"""
        expected_object_orion_id = f'{self.obj.orion_id}'
        self.assertEqual(expected_object_orion_id, '12345')

    def test_addresses_content(self):
        """testing addresses field"""
        expected_object_addresses = f'{self.obj.addresses}'
        self.assertEqual(expected_object_addresses, '10.10.10.10')

    def test_common_name_content(self):
        """testing common_name field"""
        expected_object_common_name = f'{self.obj.common_name}'
        self.assertEqual(expected_object_common_name, 'A Common Name')

    def test_organization_name_content(self):
        """testing organization_name field"""
        exp_obj_org_name = f'{self.obj.organization_name}'
        self.assertEqual(exp_obj_org_name, 'A Great IT Place')

    def test_country_name_content(self):
        """testing country_name field"""
        expected_object_country_name = f'{self.obj.country_name}'
        self.assertEqual(expected_object_country_name, 'Canada')

    def test_sig_algo(self):
        """testing sig_algo field"""
        expected_object_sig_algo = f'{self.obj.sig_algo}'
        self.assertEqual(expected_object_sig_algo, 'sha256WithRSAEncryption')

    def test_bits(self):
        """testing bits field"""
        expected_object_bits = f'{self.obj.bits}'
        self.assertEqual(expected_object_bits, '2048')

    def test_md5(self):
        """testing md5 field"""
        expected_object_md5 = f'{self.obj.md5}'
        self.assertEqual(expected_object_md5, '57adc7886d93a03d934ae691178748b7')

    def test_sha1(self):
        """testing sha1 field"""
        expected_object_sha1 = f'{self.obj.sha1}'
        self.assertEqual(expected_object_sha1, 'ae699d5ebddce6ed574111262f19bb18efbe73b0')

    def test_save(self):
        """testing save record"""
        NmapCertsData.objects.filter(md5="57adc7886d93a03d934ae691178748b7").update(bits="1024")
        bits_entry = NmapCertsData.objects.filter(md5="57adc7886d93a03d934ae691178748b7")
        for fld in bits_entry:
            self.assertEqual(fld.bits, '1024')
        NmapCertsData.objects.filter(md5="57adc7886d93a03d934ae691178748b7").update(bits="2048")
        bits_entry = NmapCertsData.objects.filter(md5="57adc7886d93a03d934ae691178748b7")
        for fld in bits_entry:
            self.assertEqual(fld.bits, '2048')
