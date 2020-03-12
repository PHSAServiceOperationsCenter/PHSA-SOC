"""
p_soc_auto_base.tests
---------------------

This module contains tests for functionality shared across the
:ref:`SOC Automation Server`.

:copyright:

    Copyright 2020 - Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.test import TestCase

from mail_collector.models import DomainAccount
from p_soc_auto_base.models import BaseModel
from p_soc_auto_base.test_lib import UserTestCase


class BaseModelTest(TestCase):
    """
    Tests for base model.
    """
    def test_getorcreateuser(self):
        """
        Tests tha getorcreateuser does create a user.
        :return:
        """
        test_user = BaseModel.get_or_create_user('testuser')
        self.assertTrue(
            get_user_model().objects.filter(username='testuser').exists())
        test_user.delete()


class DefaultTest(UserTestCase):
    """
    Tests for BaseModelWithDefaultInstance
    """
    def test_createtwodefaults_throwsexception(self):
        """
        Tests that trying to create two default instances causes an error.
        """
        DomainAccount.objects.update(is_default=False)

        # using a private function to create the DomainAccount allows us to use
        # assertRaises
        def create_default():
            DomainAccount.objects.create(
                is_default=True, domain='testdomain', username='testuser',
                password='testword', **self.USER_ARGS
            )
        create_default()
        self.assertRaises(ValidationError, create_default)

    def test_default_returnsobj(self):
        """
        Test that the default function gets the object.
        """
        self.assertIsInstance(DomainAccount.default(), DomainAccount)

    def test_getdefault_returnsint(self):
        """
        Test that the get_default function gets the id of the object.
        """
        self.assertIsInstance(DomainAccount.get_default(), int)
