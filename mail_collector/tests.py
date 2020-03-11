"""
mail_collector.tests
--------------------

This module contains tests for the mail collector module.

:copyright:

    Copyright 2020 - Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from mail_collector.models import DomainAccount, ExchangeConfiguration
from p_soc_auto_base.test_lib import UserTestCase

from hypothesis import given
from hypothesis.strategies import text, characters


# TODO tests for all proxymanagers? (is this just testing Django?)


class DomainAccountTest(UserTestCase):
    """
    Tests for :class:`mail_collector.models.DomainAccount`
    """
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        DomainAccount.objects.all().update(is_default=False)

    @given(domain_name=text(characters(whitelist_categories=('Lu', 'Ll', 'Nd',),
                                       whitelist_characters=('_', '-',),
                                       min_codepoint=0, max_codepoint=128),
                            min_size=1, max_size=15))
    def test_createdomainaccount_domainisuppercase(self, domain_name):
        """
        Test that domain accounts follow windows conventions for domain names.
        """
        domain = DomainAccount.objects.create(
            domain=domain_name, username='name', password='word',
            **self.USER_ARGS
        )
        self.assertEqual(domain.domain, domain_name.upper())
        domain.delete()


class ExchangeConfigurationTest(UserTestCase):
    """
    Tests for :class:`mail_collector.models.ExchangeConfiguration`
    """
    @given(subject=text(min_size=1, max_size=78))
    def test_clean_emailsubjecthasnolinebreaks(self, subject):
        """
        Test that domain accounts remove line breaks from email subjects.
        """
        config = ExchangeConfiguration.objects.create(
            email_subject=subject, config_name='test', **self.USER_ARGS
        )
        self.assertNotIn('\r', config.email_subject)
        self.assertNotIn('\n', config.email_subject)
