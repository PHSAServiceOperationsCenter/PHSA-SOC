"""
.. _fixtures:

pytest fixtures for the p_soc_auto applications unit tests

:module:    p_soc_auto.testlib.fixtures

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Oct. 11, 2018

"""
import pytest

from django.utils import timezone

from .factories import RuleAppliesFactory, ExpirationRuleFactory, RuleDemoDataFactory


unexpired_fixtures = []
healthy_fixtures = []
warning_fxtures = []

not_yet_valid = [
    dict(data_name='not yet valid 1 year',
         data_datetime_1=timezone.now() + timezone.timedelta(days=365),
         data_datetime_2=timezone.now() + timezone.timedelta(days=366)),
    dict(data_name='not yet valid 1 day',
         data_datetime_1=timezone.now() + timezone.timedelta(days=1),
         data_datetime_2=timezone.now() + timezone.timedelta(days=366)),
    dict(data_name='not yet valid less than 1 day',
         data_datetime_1=timezone.now() + timezone.timedelta(hours=23),
         data_datetime_2=timezone.now() + timezone.timedelta(days=366)),
    dict(data_name='not yet valid 1 hour',
         data_datetime_1=timezone.now() + timezone.timedelta(hours=1),
         data_datetime_2=timezone.now() + timezone.timedelta(days=366)),
    dict(data_name='not yet valid less than 1 hour',
         data_datetime_1=timezone.now() + timezone.timedelta(minutes=41),
         data_datetime_2=timezone.now() + timezone.timedelta(days=366)), ]


@pytest.fixture(params=not_yet_valid)
def not_yet_valid_rule_and_demo_data(request, db):
    """
    pytest fixture that creates an expiration rule and rule demo data
    to trigger "not yet valid" alerts
    """
    import ipdb
    ipdb.set_trace()
    RuleAppliesFactory.create(
        rule=ExpirationRuleFactory.create(rule='not yet valid'))

    RuleDemoDataFactory.create(**request.param)

    return request.param.get('data_name')
