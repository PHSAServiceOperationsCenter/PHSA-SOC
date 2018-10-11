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
import random
import string

from datetime import timedelta

import factory
import names

from dateutil import parser as datetime_parser
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


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


class RuleDemoDataFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'rules_engine.RuleDemoData'

    data_name = factory.Sequence(lambda n: 'data_demo_entry_%03d' % n)
    data_datetime_1 = timezone.make_aware(datetime_parser.parse('1970'))
    data_datetime_2 = timezone.make_aware(datetime_parser.parse('2030'))
    data_number_1 = random.randint(1, 100)
    data_number_2 = random.randint(1, 100)
    data_string_1 = ''.join(
        random.choice(string.ascii_lowercase) for x in range(16))
    data_string_2 = ''.join(
        random.choice(string.ascii_lowercase) for x in range(16))
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)


class RuleFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'rules_engine.Rule'

    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)

    rule = factory.Sequence(lambda n: 'rule_%03d' % n)

    @factory.lazy_attribute
    def subscribers(self):
        subscribers = []
        for _ in range(random.randint(1, 4)):
            subscribers.append(
                '{}.{}@phsa.ca'.format(names.get_first_name().lower(),
                                       names.get_last_name().lower()))

        return ','.join(subscribers)

    @factory.lazy_attribute
    def escalation_subscribers(self):
        escalation_subscribers = []
        for _ in range(random.randint(1, 4)):
            escalation_subscribers.append(
                '{}.{}@phsa.ca'.format(names.get_first_name().lower(),
                                       names.get_last_name().lower()))

        return ','.join(escalation_subscribers)


class RegexRuleFactory(RuleFactory):
    class Meta:
        model = 'rules_engine.RegexRule'

    match_string = 'match me'


class IntervalRuleFactory(RuleFactory):
    class Meta:
        model = 'rules_engine.IntervalRule'


class ExpirationRuleFactory(RuleFactory):
    class Meta:
        model = 'rules_engine.ExpirationRule'

    grace_period = timedelta(days=666, hours=666, minutes=666, seconds=666)


class RuleAppliesFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'rules_engine.RuleApplies'

    rule = factory.SubFactory(RuleFactory)
    content_type = factory.iterator(
        ContentType.objects.filter(model='ruledemodata'))
    field_name = 'data_datetime_1'
    second_field_name = 'data_datetime_2'

    @factory.lazy_attribute
    def subscribers(self):
        subscribers = []
        for _ in range(random.randint(1, 4)):
            subscribers.append(
                '{}.{}@phsa.ca'.format(names.get_first_name().lower(),
                                       names.get_last_name().lower()))

        return ','.join(subscribers)

    @factory.lazy_attribute
    def escalation_subscribers(self):
        escalation_subscribers = []
        for _ in range(random.randint(1, 4)):
            escalation_subscribers.append(
                '{}.{}@phsa.ca'.format(names.get_first_name().lower(),
                                       names.get_last_name().lower()))

        return ','.join(escalation_subscribers)
