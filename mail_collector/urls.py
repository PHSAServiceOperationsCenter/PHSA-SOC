"""
.. _urls:

:module:    mail_collector.urls

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    aug. 9, 2019

URL mappings for the :ref:`Mail Collector Application`

"""
from django.urls import path

from mail_collector import api

urlpatterns = [
    path(r'api/get_config/<str:host_name>/', api.get_bot_config)
]
