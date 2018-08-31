"""
django models for the ssl_certificates app

:module:    ssl_certificates.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""

from django.conf.urls import url
from  .import views

urlpatterns = [
    url(r'^$', views.index, name="index"),
]
