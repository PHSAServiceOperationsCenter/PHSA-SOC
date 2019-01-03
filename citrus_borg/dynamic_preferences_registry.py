"""
.. _dynamic_preferences_registry:

dynamic preferences for the citrus_borg app

:module:    citrus_borg.dynamic_preferences_registry

:copyright:

    Copyright 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    jan. 3, 2019

"""
from django.utils.translation import gettext_lazy as _

from dynamic_preferences.types import (
    BooleanPreference, StringPreference, DurationPreference,
)
from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
