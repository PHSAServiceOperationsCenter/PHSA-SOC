"""
mail_collector.preferences
--------------------------

This module is used to provide run-time configurable settings.

See p_soc_auto_base.preferences for more info.

:copyright:

    Copyright 2021 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import BooleanPreference, DurationPreference, \
    StringPreference

EXCHANGE = Section('exchange',
                   verbose_name=_(
                       'Options for the PHSA Service Operations Center'
                       ' Exchange Monitoring Application').title())


@global_preferences_registry.register
class ExchangeExpireEvents(DurationPreference):
    """
    Dynamic preferences class controlling how old an event collected by the
    :ref:`Mail Collector Application` must be before it will be marked
    as expired

    :access_key: 'exchange__expire_events`
    """
    section = EXCHANGE
    name = 'expire_events'
    default = timezone.timedelta(hours=36)
    """default setting value"""
    required = True
    verbose_name = _('Exchange events older than')
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class ExchangeReportingInterval(DurationPreference):
    """
    Dynamic preferences class controlling the time interval used by the
    :ref:`Mail Collector Application` for generating reports

    :access_key: 'exchange__report_interval'
    """
    section = EXCHANGE
    name = 'report_interval'
    default = timezone.timedelta(hours=12)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange reporting interval')
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class ExchangeReportErrorLevel(StringPreference):
    """
    Dynamic preferences class controlling the error level used by the
    :ref:`Mail Collector Application` when generating reports

    :access_key: 'exchange__report_level'
    """
    section = EXCHANGE
    name = 'report_level'
    default = 'INFO'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Error level for all Exchange reports')
    """verbose name of this dynamic preference"""
    help_text = format_html(
        "{}", _('a report does not really have an error level but we need'
                ' a value here than can be empty, i.e. no level in order'
                ' to reuse existing mail templates'))


@global_preferences_registry.register
class ExchangeDeleteExpired(BooleanPreference):
    """
    Dynamic preferences class controlling whether expired event collected by
    the :ref:`Mail Collector Application` will be deleted

    :access_key: `exchange__delete_expired`
    """
    section = EXCHANGE
    name = 'delete_expired'
    default = True
    """default value for this dynamic preference"""
    required = False
    verbose_name = _('Delete expired Exchange events')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class ExchangeSendEmptyAlerts(BooleanPreference):
    """
    Dynamic preferences class controlling whether emails are being sent
    by the :ref:`Mail Collector Application` when an alert is not being
    raised. This the opposite of the `No news is good news
    <https://www.phrases.org.uk/bulletin_board/45/messages/366.html>`_ phrase

    :access_key: 'exchange__empty_alerts'
    """
    section = EXCHANGE
    name = 'empty_alerts'
    default = False
    """default value for this dynamic preference"""
    required = False
    verbose_name = _('Always Send Email Alerts')
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('send email notifications even when there are no alerts'))


@global_preferences_registry.register
class ExchangeDefaultErrorLevel(StringPreference):
    """
    Dynamic preferences class controlling the error level used by the
    :ref:`Mail Collector Application` when sending alerts for which no
    error level was specified

    :access_key: 'exchange__default_level`
    """
    section = EXCHANGE
    name = 'default_level'
    default = 'WARNING'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Default error level for Exchange alerts')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class ExchangeEventSource(StringPreference):
    """
    Dynamic preferences class that provides the key used by the
    :ref:`Mail Collector Application` data collection to identify
    events of interest

    :access_key: 'exchange__source'
    """
    section = EXCHANGE
    name = 'source'
    default = 'BorgExchangeMonitor'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Windows Logs Source for Exchange Monitoring Events ')
    """verbose name for this dynamic preference"""
    help_text = _(
        'This is a list of values. Use "," to separate the list items')


@global_preferences_registry.register
class ExchangeServerWarn(DurationPreference):
    """
    Dynamic preferences class controlling how long the
    :ref:`Mail Collector Application` will wait before raising a warning
    about an Exchange entity not providing Exchange services

    :access_key: 'exchange__server_warn'
    """
    section = EXCHANGE
    name = 'server_warn'
    default = timezone.timedelta(hours=2)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange server warnings after').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('raise warning about an Exchange server if it has not been'
                ' seen for longer than this time period'))


@global_preferences_registry.register
class ExchangeServerError(DurationPreference):
    """
    Dynamic preferences class controlling how long the
    :ref:`Mail Collector Application` will wait before raising an error
    about an Exchange entity not providing Exchange services

    :access_key: 'exchange__server_error'
    """
    section = EXCHANGE
    name = 'server_error'
    default = timezone.timedelta(hours=6)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange server errors after').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('raise error about an Exchange server if it has not been'
                ' seen for longer than this time period'))


@global_preferences_registry.register
class ExchangeDeadBotWarn(DurationPreference):
    """
    Dynamic preferences class controlling how long the
    :ref:`Mail Collector Application` will wait before raising a warning
    about an Exchange monitoring bot not sending any Exchange events

    :access_key: 'exchange__bot_warn'
    """
    section = EXCHANGE
    name = 'bot_warn'
    default = timezone.timedelta(hours=2)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange client bot warnings after').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('raise warning about an Exchange client bot if it has not been'
                ' seen for longer than this time period'))


@global_preferences_registry.register
class ExchangeNilDuration(DurationPreference):
    """
    Dynamic preferences class providing a 0 duration for internal use
    within the :ref:`Mail Collector Application`

    :access_key: 'exchange__nil_duration'

    """
    section = EXCHANGE
    name = 'nil_duration'
    default = timezone.timedelta(hours=0)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('nil duration').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('some filters will not work if there is no time interval'
                ' baked in. if we want to reuse these filters without'
                ' worrying about the time interval we can use this'))


@global_preferences_registry.register
class ExchangeDeadBotError(DurationPreference):
    """
    Dynamic preferences class controlling how long the
    :ref:`Mail Collector Application` will wait before raising an error
    about an Exchange monitoring bot not sending any Exchange events

    :access_key: 'exchange__bot_error'
    """
    section = EXCHANGE
    name = 'bot_error'
    default = timezone.timedelta(hours=6)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange client bot errors after').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('raise error about an Exchange client bot if it has not been'
                ' seen for longer than this time period'))


@global_preferences_registry.register
class ExchangeDefaultError(DurationPreference):
    """
    Dynamic preferences class controlling how long the
    :ref:`Mail Collector Application` will wait before raising an error
    about unspecified items

    :access_key: 'exchange__bot_error'

    """
    section = EXCHANGE
    name = 'default_error'
    default = timezone.timedelta(hours=2)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('exchange errors after (default)').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}", _('fallback error configuration for all exchange entities'))
