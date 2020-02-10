"""
"""
__updated__ = '2018_08_07'

from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class PSocAutoBaseConfig(AppConfig):
    """
    App class for the base application
    """
    name = 'p_soc_auto_base'
    verbose_name = _('PHSA Service Operations Center Base Application')
