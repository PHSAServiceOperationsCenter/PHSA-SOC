"""
.. _urlss:

django urlss for the rules_engine app

:module:    p_soc_auto.rules_engine.urlss

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    sep. 19, 2018

"""
from django.conf.urls import url
from .views import RuleAppliesAutocomplete

urlpatterns = [
    url(r'autocomplete-field-name/$',
        RuleAppliesAutocomplete.as_view(), name='autocomplete-field-name'), ]
