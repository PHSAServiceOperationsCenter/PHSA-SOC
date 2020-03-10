"""
orion_integration.tests
-----------------------

This module contains tests for the orion integration module.

:copyright:

    Copyright 2020 - Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from django.test import TestCase

from orion_integration.models import OrionNode, OrionNodeCategory, \
    OrionAPMApplication
from p_soc_auto_base.test_lib import UserTestCase


# TODO test that running update or create from orion creates objects that then
#      return true when running exists in orion?


class OrionBaseModelTest(UserTestCase):
    """
    Tests for the OrionBaseModel functions.
    We test using OrionNodeCategory since OrionBaseModel is abstract
    """
    def test_existsinorion_exists(self):
        """
        Test that calling exists in orion for a category that exists returns
        true
        """
        test_obj =OrionNodeCategory.objects.create(
            orion_id=0, category='Network', **self.USER_ARGS)
        self.assertTrue(test_obj.exists_in_orion())
        test_obj.delete()

    def test_existsinorion_fake(self):
        """
        Test that exists in orion returns false for a nonexistent category
        """
        test_obj = OrionNodeCategory.objects.create(
            orion_id=3253, category='Fake', **self.USER_ARGS)
        self.assertFalse(test_obj.exists_in_orion())

    def test_updateorcreatefromorion(self):
        """
        Test that update or create from orion runs successfully
        """
        self.assertEqual(
            OrionNodeCategory.update_or_create_from_orion()['errored_records'],
            0
        )


class OrionNodeTest(TestCase):
    """
    Tests for OrionNode
    """
    def test_update_or_create_from_orion(self):
        """
        Test that update or create from orion runs successfully for Orion Node
        """
        self.assertEqual(
            OrionNode.update_or_create_from_orion()[-1]['errored_records'], 0)


class OrionAPMApplicationTest(TestCase):
    """
    Tests for OrionAPMApplication
    """
    def test_updateorcreatefromorion(self):
        """
        Test that update or create from orion runs successfully for
        OrionAPMAplication
        """
        self.assertEqual(
            OrionAPMApplication.update_or_create_from_orion()
            [-1]['errored_records'], 0)
