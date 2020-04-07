"""
.. _api:

:module:    mail_collector.api

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

REST end-points for the :ref:`Mail Collector Application`

"""
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from citrus_borg.models import WinlogbeatHost
from mail_collector.models import ExchangeConfiguration
from mail_collector.serializers import BotConfigSerializer


@api_view(['GET', ])
def get_bot_config(request, host_name):
    """
    get the exchange client configuration

    :param request: an HTTP GET request
    :param host_name: the short host name for the bot that is
                          requesting a configuration
    :type host_name: str

    :returns:

        the bot config JSON encoded if available, or a default configuration
        also JSON encoded when the host_name is not known to the
        server. if neither configurations are available,
        an HTTP 404 (not found) error is returned

    :rtype: :class:`rest_framework.response.Response`

    """
    queryset = WinlogbeatHost.objects.filter(host_name__iexact=host_name)

    if not queryset.exists():
        return Response(f'Bot at {host_name} is not recognized by the '
                        f'Exchange monitoring client.',
                        status=status.HTTP_404_NOT_FOUND)

    bot = queryset.get()

    if bot.exchange_client_config is None:
        try:
            exchange_client_config = ExchangeConfiguration.objects.filter(
                is_default=True).get()
        except ExchangeConfiguration.DoesNotExist:
            return Response(
                (f'Bot at {host_name} does not have a configuration for the '
                 f'Exchange monitoring client.'),
                status=status.HTTP_404_NOT_FOUND)

        bot.exchange_client_config = exchange_client_config
        bot.save()

    serializer = BotConfigSerializer(queryset, many=True)
    return Response(serializer.data, status=status.HTTP_200_OK)
