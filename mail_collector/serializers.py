"""
.. _serializers:

:module:    mail_collector.serializers

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

REST serializers for the :ref:`Mail Collector Application`

"""
from rest_framework import serializers

from mail_collector.models import (
    DomainAccount, ExchangeAccount, WitnessEmail, ExchangeConfiguration,
    MailSite, MailHost,
)


# Serializers don't require methods, they are data classes.
# pylint: disable=too-few-public-methods
class DomainAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`mail_collector.models.DomainAccount`

    This is a read-only serializer.
    """
    domain = serializers.CharField(max_length=15)
    username = serializers.CharField(max_length=64)
    password = serializers.CharField(max_length=64)

    class Meta:
        model = DomainAccount
        fields = ('domain', 'username', 'password', )


class ExchangeAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`mail_collector.models.ExchangeAccount`

    This is a read-only serializer.
    """
    smtp_address = serializers.EmailField()
    domain_account = DomainAccountSerializer()
    exchange_autodiscover = serializers.BooleanField()
    autodiscover_server = serializers.CharField(max_length=253)

    class Meta:
        model = ExchangeAccount
        fields = ('smtp_address', 'domain_account',
                  'exchange_autodiscover', 'autodiscover_server')


class WitnessEmailSerializer(serializers.ModelSerializer):
    """
    Serialzer for :class:`mail_collector.models.WitnessEmail`

    This is a read-only serializer.
    """
    smtp_address = serializers.EmailField()

    class Meta:
        model = WitnessEmail
        fields = ('smtp_address')


class ExchangeConfigurationSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`mail_collector.models.ExchangeConfiguration`

    This is a read-only serializer.
    """
    config_name = serializers.CharField(max_length=64)
    exchange_accounts = ExchangeAccountSerializer(many=True, read_only=True)
    debug = serializers.BooleanField()
    autorun = serializers.BooleanField()
    mail_check_period = serializers.DurationField()
    ascii_address = serializers.BooleanField()
    utf8_address = serializers.BooleanField()
    check_mx = serializers.BooleanField()
    check_mx_timeout = serializers.DurationField()
    min_wait_receive = serializers.DurationField()
    backoff_factor = serializers.IntegerField()
    max_wait_receive = serializers.DurationField()
    tags = serializers.CharField()
    email_subject = serializers.CharField(max_length=78)
    witness_addresses = WitnessEmailSerializer(many=True, read_only=True)

    class Meta:
        model = ExchangeConfiguration
        fields = ('config_name', 'exchange_accounts', 'debug', 'autorun',
                  'mail_check_period', 'ascii_address', 'utf8_address',
                  'check_mx', 'check_mx_timeout', 'min_wait_receive',
                  'backoff_factor', 'max_wait_receive', 'tags',
                  'email_subject', 'witness_addresses')


class MailSiteSerializer(serializers.ModelSerializer):
    """
    Serializer for :class:`mail_collector.models.MailSite`

    This is a read-only serializer.
    """
    site = serializers.CharField(max_length=64)

    class Meta:
        model = MailSite
        fields = ('site', )


class BotConfigSerializer(serializers.ModelSerializer):
    """
    Serializer used for passing the main configuration required for running
    an instance of the :ref:`Mail Borg Client Application` on a remote
    monitoring bot

    It combines information from
    :class:`mail_collector.models.MailHost`,
    :class:`mail_collector.models.MailSite`, and
    :class:`mail_collector.models.ExchangeConfiguration`
    """
    host_name = serializers.CharField(max_length=63)
    site = MailSiteSerializer(read_only=True)
    exchange_client_config = ExchangeConfigurationSerializer(read_only=True)

    class Meta:
        model = MailHost
        fields = ('host_name', 'site', 'exchange_client_config')
