"""
.. _urls:

urls module for the mail_collector app

:module:    mail_collector.urls

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    aug. 9, 2019

"""
from django.urls import path

from mail_collector import api

urlpatterns = [
    path(r'api/get_config/<str:host_name>/', api.get_bot_config)
]
