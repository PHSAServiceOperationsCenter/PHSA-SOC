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
from django.conf import settings
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from dynamic_preferences.types import (
    BooleanPreference, StringPreference, DurationPreference,
)
from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry

# pylint: disable=E1101
# E1101: instance of '__proxy__' has no 'title' member caused by using
# .title() on returns from gettext_lazy()


citrus_borg_common = Section(
    'citrusborgcommon', verbose_name=_('citrus borg common settings').title())
citrus_borg_events = Section(
    'citrusborgevents', verbose_name=_('citrus borg event settings').title())
citrus_borg_node = Section()
citrus_borg_ux = Section()
citrus_borg_logon = Section()


@global_preferences_registry.register
class ServiceUser(StringPreference):
    """
    service or default user preference
    """
    section = citrus_borg_common
    name = 'service_user'
    default = settings.CITRUS_BORG_SERVICE_USER
    required = True
    verbose_name = _('citrus borg service user').title()
    help_text = format_html(
        "{}<br>{}",
        _('default django user instance for background server processes.'),
        _('will be created automatically if it does not exist already'))


@global_preferences_registry.register
class SendNoNews(BooleanPreference):
    """
    send empty alerts preference
    """
    section = citrus_borg_common
    name = 'send_no_news'
    default = settings.CITRUS_BORG_NO_NEWS_IS_GOOD_NEWS
    required = True
    verbose_name = _("don't send empty citrix alert emails").title()
    help_text = format_html(
        "{}<br>{}",
        _('by default the application sends alert emails even if there is no'
          ' alert.'),
        _('enable this setting to only send alert emails if alerts have'
          ' occurred'))


@global_preferences_registry.register
class DeadAfter(DurationPreference):
    """
    reprot something as dead after preference
    """
    section = citrus_borg_common
    name = 'dead_after'
    default = settings.CITRUS_BORG_IGNORE_EVENTS_OLDER_THAN
    verbose_name = _('dead if not seen for more than').title()
    help_text = format_html(
        "{}<br>{}",
        _('report a site, bot, or session host as dead if events mentioning'),
        _('them have not been received for more than this time period'))


@global_preferences_registry.register
class IgnoreEvents(DurationPreference):
    """
    ignore events older than preference
    """
    section = citrus_borg_events
    name = 'ignore_events_older_than'
    default = settings.CITRUS_BORG_IGNORE_EVENTS_OLDER_THAN
    verbose_name = _('ignore events created older than').title()
    help_text = _(
        'events older than this value will not be used for any analysis')


@global_preferences_registry.register
class ExpireEvents(DurationPreference):
    """
    expire events older than preference
    """
    section = citrus_borg_events
    name = 'expire_events_older_than'
    default = settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER
    verbose_name = _('mark events as expired if older than').title()
    help_text = _(
        'events older than this value will be marked as expired')


@global_preferences_registry.register
class DeleteExpireEvents(BooleanPreference):
    """
    delete expired eventss preference
    """
    section = citrus_borg_events
    name = 'delete_expired_events'
    default = settings.CITRUS_BORG_DELETE_EXPIRED
    verbose_name = _('delete expired events').title()

#pylint: enable=E1101
