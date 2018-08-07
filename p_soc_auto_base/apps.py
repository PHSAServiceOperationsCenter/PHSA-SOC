"""
"""
__updated__ = '2018_08_07'

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BaseConfig(AppConfig):
    """
    App class fro the base application
    """
    name = 'base'
    verbose_name = _('PHSA Service Operations Center Base Application')
