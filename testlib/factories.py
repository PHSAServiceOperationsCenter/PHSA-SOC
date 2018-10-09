'''
Created on Oct 5, 2018

@author: serban
'''
"""
.. _factories:

data factories for the p_soc_auto applications models

:module:    p_soc_auto.testlib.factories

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Oct. 9, 2018

"""
import factory

from django.contrib.auth import get_user_model

from rules_engine.models import RuleDemoData


class UserFactory(factory.DjangoModelFactory):
    """
    factory for the User model
    """
    class Meta:
        model = get_user_model()

    first_name = factory.Faker('first_name')
    last_name = factory.Faker('last_name')
    is_superuser = False
    is_active = True
    is_staff = True

    @factory.lazy_attribute
    def username(self):
        """
        build username from firt and last name
        """
        return '{}{}'.format(
            str(self.first_name)[0].lower(), str(self.last_name).lower())

    @factory.lazy_attribute
    def email(self):
        """
        build email from username
        """
        return '{}@phsa.ca'.format(self.username)
