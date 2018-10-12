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

from .factories import RuleDemoDataFactory


@pytest.fixture(params=['not_yet_valid', 'expired', 'warning', 'healthy'])
def demo_data_for_exp_rule(request, db):
    if request.param in ['not_yet_valid']:
        data_datetime_1 = timezone.now() + timezone.timedelta(days=365)
        data_datetime_2 = timezone.now() + timezone.timedelta(days=366)

    return RuleDemoDataFactory.create(
        data_datetime_1=data_datetime_1, data_datetime_2=data_datetime_2)
