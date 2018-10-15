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

import factory
import names

from dateutil import parser as datetime_parser
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone


def get_random_emails(max_range=4, email_domain='phsa.ca'):
    """
    :returns: a string of comma separated random email addresses in the
              first_name.last_name@email.domain. the number of entries is
              random between 1 and the :arg:`<max_range.~ value
    :rtype: ``str``

    :arg int max_range: the maximuim number of email addresses
    :arg str email_domain: the email address domain component
    """
    emails = []
    for _ in range(random.randint(1, max_range)):
        emails.append('{}.{}@{}'.format(names.get_first_name().lower(),
                                        names.get_last_name().lower(),
                                        email_domain)
                      )

    return ','.join(emails)


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
        build username from first and last name
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
    """
    data factory for the :class:`<rules_enigne.models.RuleDemoData>`
    """
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
    """
    data factory for the :class:`<rules_engine.models.Rule>`
    """
    class Meta:
        model = 'rules_engine.Rule'

    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)

    rule = factory.Sequence(lambda n: 'rule_%03d' % n)

    @factory.lazy_attribute
    def subscribers(self):
        return get_random_emails()

    @factory.lazy_attribute
    def escalation_subscribers(self):
        return get_random_emails()


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

    grace_period = timezone.timedelta(
        days=666, hours=666, minutes=666, seconds=666)


class RuleAppliesFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'rules_engine.RuleApplies'

    rule = factory.SubFactory(RuleFactory)
    content_type = factory.Iterator(
        ContentType.objects.filter(model='ruledemodata'))
    field_name = 'data_datetime_1'
    second_field_name = 'data_datetime_2'
    created_by = factory.SubFactory(UserFactory)
    updated_by = factory.SubFactory(UserFactory)

    @factory.lazy_attribute
    def subscribers(self):
        return get_random_emails()

    @factory.lazy_attribute
    def escalation_subscribers(self):
        return get_random_emails()


class NotificationTypeFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'notifications.NotificationType'


class NotificationLevelFactory(factory.DjangoModelFactory):
    class Meta:
        model = 'notifications.NotificationLevel'
