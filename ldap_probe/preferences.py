"""
ldap_probe.preferences
----------------------

This module is used to provide run-time configurable settings.

See p_soc_auto_base.preferences for more info.

:copyright:

    Copyright 2021 Provincial Health Service Authority
    of British Columbia


"""
import decimal

from django.conf import settings
from django.utils import timezone
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import BooleanPreference, DecimalPreference, \
    DurationPreference, StringPreference

LDAP_PROBE = Section('ldapprobe',
                     verbose_name=_(
                         'Options for the PHSA Service Operations Center '
                         'Active Directory Services Monitoring '
                         'Application').title())


@global_preferences_registry.register
class LdapSearchBaseDNDefault(StringPreference):
    """
    Dynamic preferences class controlling the default value for the
    base DN argument used by LDAP search functions

    For example, an LDAP search for the `LoginPI01` account can  be initiated
    from `'dc=vch,dc=ca'`.

    :access_key: 'ldapprobe__search_dn_default'
    """
    section = LDAP_PROBE
    name = 'search_dn_default'
    default = 'dc=vch,dc=ca'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Default search base DN').title()
    """verbose name for this dynamic preference"""
    help_text = format_html(
        "{}<br>{}",
        _('Default value for the base DN argument used by'),
        _('LDAP search functions'))


@global_preferences_registry.register
class LdapServiceUser(StringPreference):
    """
    Dynamic preferences class controlling the service user to be used by
    :ref:`Active Directory Services Monitoring Application` background
    processes

    :access_key: 'ldapprobe__service_user'
    """
    section = LDAP_PROBE
    name = 'service_user'
    default = 'ldap_probe_service_user'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Service user for Domain Controllers Monitoring Application'
        ' background processes').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapExpireProbeLogEntries(DurationPreference):
    """
    Dynamic preferences class controlling how old `LDAP` probe log entries
    are before they are marked as `expired`

    :access_key: 'ldapprobe__ldap_expire_after'
    """
    section = LDAP_PROBE
    name = 'ldap_expire_after'
    default = settings.CITRUS_BORG_EVENTS_EXPIRE_AFTER
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'mark LDAP probe log entries as expired if older than').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapDeleteExpiredProbeLogEntries(BooleanPreference):
    """
    Dynamic preferences class controlling whether `expired` `LDAP` probe
    log entries will be deleted

    :access_key: 'ldapprobe__ldap_delete_expired'
    """
    section = LDAP_PROBE
    name = 'ldap_delete_expired'
    default = settings.CITRUS_BORG_DELETE_EXPIRED
    """default value for this dynamic preference"""
    required = False
    verbose_name = _('delete expired LDAP probe log entries').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapErrorAlertSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` error alerts

    :access_key: 'ldapprobe__ldap_error_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_error_subscription'
    default = 'LDAP: Error alerts subscription'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Email Subscription for LDAP Error Alerts').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapErrorReportSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` error reports

    :access_key: 'ldapprobe__ldap_error_report_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_error_report_subscription'
    default = 'LDAP: Error report'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Email Subscription for LDAP Error Reports').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapNonOrionADNodesReportSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` reports about `AD` nodes not defined
    on the `Orion` server

    :access_key: 'ldapprobe__ldap_non_orion_ad_nodes_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_non_orion_ad_nodes_subscription'
    default = 'LDAP: non Orion AD nodes'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Email Subscription for non Orion AD Nodes Reports').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapOrionADNodesFQDNReportSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` reports about `AD` nodes defined
    on the `Orion` server with missing FQDN values

    :access_key: 'ldapprobe__ldap_orion_fqdn_ad_nodes_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_orion_fqdn_ad_nodes_subscription'
    default = 'LDAP: Orion FQDN AD nodes'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Email Subscription for Orion AD Nodes FQDN Reports').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapOrionADNodesDupesReportSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` reports about duplicate `AD` nodes defined
    on the `Orion` server

    :access_key: 'ldapprobe__ldap_orion_dupes_ad_nodes_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_orion_dupes_ad_nodes_subscription'
    default = 'LDAP: Duplicate Orion AD nodes'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Email Subscription for duplicate Orion AD Nodes Reports').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfAlertSubscription(StringPreference):
    """
    Dynamic preferences class controlling the name of the
    :class:`Email subscription <p_soc_auto_base.models.Subscription>`
    used for dispatching `LDAP` performance alerts

    :access_key: 'ldapprobe__ldap_perf_subscription'
    """
    section = LDAP_PROBE
    name = 'ldap_perf_subscription'
    default = 'LDAP: Performance alerts subscription'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('Email Subscription for LDAP Performance Alerts').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfRaiseMinorAlerts(BooleanPreference):
    """
    Dynamic preferences class controlling whether minor alerts about AD
    services performance degradations will be raised

    By default, only response times larger than the value specified via
    :class:`LdapPerfNeverExceedThreshold` will trigger an alert. Response
    times larger than values defined by :class:`LdapPerfAlertThreshold` and
    :class:`LdapPerfWarnThreshold` will only be included in periodic
    reports with regards to performance degradation.

    :access_key: 'ldapprobe__ldap_perf_raise_all'
    """
    section = LDAP_PROBE
    name = 'ldap_perf_raise_all'
    default = False
    """default value for this dynamic preference"""
    required = False
    verbose_name = _(
        'Raise alerts for all LDAP performance degradation events.').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfDegradationReportGoodNews(BooleanPreference):
    """
    Dynamic preferences class controlling whether performance degradation
    reports with 'all is well, there is no performance degradation' will
    still be sent out via email

    :access_key: 'ldapprobe__ldap_perf_send_good_news'
    """
    section = LDAP_PROBE
    name = 'ldap_perf_send_good_news'
    default = False
    """default value for this dynamic preference"""
    required = False
    verbose_name = _(
        'LDAP: Send performance degradation reports even when there is no'
        ' performance degradation')
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfNeverExceedThreshold(DecimalPreference):
    """
    Dynamic preferences class controlling the threshold
    used for dispatching red level alerts about `LDAP` performance degradation

    :access_key: 'ldapprobe__ldap_perf_err'
    """
    section = LDAP_PROBE
    name = 'ldap_perf_err'
    default = decimal.Decimal('1.000')
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'LDAP Performance Error Threshold for Immediate Alerts (in seconds)'
    ).title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfAlertThreshold(DecimalPreference):
    """
    Dynamic preferences class controlling the threshold
    used for generating error reports for `LDAP` performance degradation

    :access_key: 'ldapprobe__ldap_perf_alert'

    .. note::

        we are aware that the class name and the access keys for this class
        and :class:`LdapPerfNeverExceedThreshold` are not following the
        usual practice.
    """
    section = LDAP_PROBE
    name = 'ldap_perf_alert'
    default = decimal.Decimal('0.750')
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'LDAP Performance Error Threshold for Reports (in seconds)').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapPerfWarnThreshold(DecimalPreference):
    """
    Dynamic preferences class controlling the threshold
    used for generating warning reports for `LDAP` performance degradation

    :access_key: 'ldapprobe__ldap_perf_warn'
    """
    section = LDAP_PROBE
    name = 'ldap_perf_warn'
    default = decimal.Decimal('0.500')
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'LDAP Performance Warning Threshold for Reports (in seconds)').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class LdapReportPeriod(DurationPreference):
    """
    Dynamic preferences class controlling the period used for generating
    `LDAP` reports

    :access_key: 'ldapprobe__ldap_reports_period'
    """
    section = LDAP_PROBE
    name = 'ldap_reports_period'
    default = timezone.timedelta(hours=1)
    """default value for this dynamic preference"""
    required = True
    verbose_name = _(
        'Time interval to use when generating LDAP reports').title()
    """verbose name for this dynamic preference"""
