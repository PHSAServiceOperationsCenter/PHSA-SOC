"""
.. _api:

REST API for the mail_collector app

:module:    mail_collector.api

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    aug. 9, 2019

"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from mail_collector.models import MailHost, ExchangeConfiguration
from mail_collector.serializers import BotConfigSerializer


@api_view(['GET', ])
def get_bot_config(request, host_name):
    """
    get the exchange client configuration

    :arg ``str`` host_name:

        the short host name for the bot that is requesting a configuration

    :returns: the bot config JSON encoded
    :rtype: :class: rest_framework.response.Response
    """
    queryset = MailHost.objects.filter(host_name__iexact=host_name)

    if not queryset.exists():
        # bot doesn't exist yet, return the default configuration
        queryset = MailHost.objects.filter(host_name__iexact='host.not.exist')
        serializer = BotConfigSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    bot = queryset.get()
    if bot.exchange_client_config is None:
        # bot exists but it doesn't have a configuration
        # assign the default configuration and refresh the queryset
        try:
            exchange_client_config = ExchangeConfiguration.objects.filter(
                is_default=True).get()
        except ExchangeConfiguration.DoesNotExist:
            return Response(
                ('Bot at %s does not have a configuration for the Exchange'
                 ' monitoring client.' % host_name),
                status=status.HTTP_406_NOT_ACCEPTABLE)

        bot.exchange_client_config = exchange_client_config
        bot.save()
        queryset = MailHost.objects.filter(host_name__iexact=host_name)

    serializer = BotConfigSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
