"""
sftp.preferences
----------------

This module is used to provide run-time configurable settings.

See p_soc_auto_base.preferences for more info.

:copyright:

    Copyright 2021 Provincial Health Service Authority
    of British Columbia

"""

from django.utils.translation import gettext_lazy as _

from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import StringPreference

SFTP_DEFAULTS = Section(
    'sftp',
    verbose_name=_('Settings used to interact with the sftp server').title())


@global_preferences_registry.register
class SFTPAccount(StringPreference):
    """
    Dynamic preferences class for the user used to login for sftp tests

    :access_key: 'sftp__username'
    """
    section = SFTP_DEFAULTS
    name = 'username'
    default = 'LoginPI25@vch.ca'
    required = True
    verbose_name = _('The user that is used to login into SFTP server.')


@global_preferences_registry.register
class SFTPPassword(StringPreference):
    """
    Dynamic preferences class for the password used to login for sftp tests

    :access_key: 'sftp__password'
    """
    section = SFTP_DEFAULTS
    name = 'password'
    default = 'LoginPI1!'
    required = True
    verbose_name = _('The password that is used to login into SFTP server.')
