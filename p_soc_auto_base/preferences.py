"""
p_soc_auto_base.preferences
---------------------------

This module is used to provide run-time configurable settings.

Each class in the module is a dynamic preference and each dynamic preference
can be configured via the `Global preferences admin interface
<../../../admin/dynamic_preferences/globalpreferencemodel/>`_ using the value
of the ``verbose_name`` attribute of the class.

To access the value of a given dynamic setting, use the :func:`get_preference`
function. For example:

.. code-block:: python

    from p_soc_auto_base.preferences import get_preference

    get_preference('exchange__report_interval')
    datetime.timedelta(1, 43200)


Running manage.py will complain that only the preferences in this file are
registered, but that is incorrect. The other preferences simply have not been
registered when the check with the database is made, but are registered later.
Surpressing this mistaken error message is an open issue.

:copyright:

    Copyright 2021 Provincial Health Service Authority
    of British Columbia



"""

from dynamic_preferences.preferences import Section
from dynamic_preferences.registries import global_preferences_registry
from dynamic_preferences.types import IntPreference, StringPreference

from django.utils.translation import gettext_lazy as _

EMAIL_PREFS = Section('emailprefs', verbose_name=_(
    'Email preferences').title())

COMMON_ALERT_ARGS = Section(
    'commonalertargs',
    verbose_name=_(
        'Common Args for Alerts Raised by the PHSA'
        ' Service Operations Center Automation Server'))
"""
dynamic user preferences section for preferences common to all applications
in the :ref:`SOC Automation Project`
"""


@global_preferences_registry.register
class EmailFromWhenDebug(StringPreference):
    """
    Dynamic preferences class controlling the `FROM:` email address used by the
    :class:`ssl_cert_tracker.lib.Email` class when sending emails in `DEBUG`
    mode

    This preference applies to all the applications in the project.

    :access_key: 'emailprefs__from_email'
    """
    section = EMAIL_PREFS
    name = 'from_email'
    default = 'daniel.busto@phsa.ca'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('originating email address when in DEBUG mode').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class EmailToWhenDebug(StringPreference):
    """
    Dynamic preferences class controlling the `TO:` email address used by the
    :class:`ssl_cert_tracker.lib.Email` class when sending emails in `DEBUG`
    mode

    This preference applies to all the applications in the project.

    :access_key: 'emailprefs__to_emails'
    """
    section = EMAIL_PREFS
    name = 'to_emails'
    default = 'daniel.busto@phsa.ca,james.reilly@phsa.ca'
    """default value for this dynamic preference"""
    required = True
    verbose_name = _('destination email addresses when in DEBUG mode').title()
    """verbose name for this dynamic preference"""


@global_preferences_registry.register
class AlertArgsErrorLevel(StringPreference):
    """
    Dynamic preferences class controlling the value used for indicating
    if an alert is considered an `ERROR` alert

    This preference should be shared among :ref:`SOC Automation Server`
    applications.

    :access_key: 'commonalertargs__error_level'

    .. todo::

        Refactor all uses of alert and report levels to use this, and related,
        dynamic preferences.

    """
    section = COMMON_ALERT_ARGS
    name = 'error_level'
    default = 'ERROR'
    """default setting value"""
    required = True
    verbose_name = _('Tag for identifying ERROR alerts and/or reports').title()
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class AlertArgsWarnLevel(StringPreference):
    """
    Dynamic preferences class controlling the value used for indicating
    if an alert is considered a `WARNING` alert

    This preference should be shared among :ref:`SOC Automation Server`
    applications.

    :access_key: 'commonalertargs__warn_level'

    """
    section = COMMON_ALERT_ARGS
    name = 'warn_level'
    default = 'WARNING'
    """default setting value"""
    required = True
    verbose_name = _('Tag for identifying WARNING alerts and/or reports').title()
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class AlertArgsInfoLevel(StringPreference):
    """
    Dynamic preferences class controlling the value used for indicating
    if an alert is considered an `INFO` alert

    This preference should be shared among :ref:`SOC Automation Server`
    applications.

    :access_key: 'commonalertargs__info_level'

    """
    section = COMMON_ALERT_ARGS
    name = 'info_level'
    default = 'INFO'
    """default setting value"""
    required = True
    verbose_name = _('Tag for identifying INFO alerts and/or reports').title()
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class AlertArgsCriticalLevel(StringPreference):
    """
    Dynamic preferences class controlling the value used for indicating
    if an alert is considered an `CRITICAL` alert

    This preference should be shared among :ref:`SOC Automation Server`
    applications.

    :access_key: 'commonalertargs__crit_level'

    """
    section = COMMON_ALERT_ARGS
    name = 'crit_level'
    default = 'CRITICAL'
    """default setting value"""
    required = True
    verbose_name = _('Tag for identifying CRITICAL alerts and/or reports').title()
    """verbose name of this dynamic preference"""


@global_preferences_registry.register
class ExternalTaskPeriod(StringPreference):
    """
    Dynamic preference to store the period that is too long a gap between
    running tasks that are not controlled by celery

    :access_key: 'commonalertargs__external_task_period'
    """
    section = COMMON_ALERT_ARGS
    name = 'external_task_period'
    default = 'minutes'
    required = True
    verbose_name = _('The expected longest wait between instances of events '
                     'whose period is set externally (to the django app).').title()


@global_preferences_registry.register
class ExternalTaskEvery(IntPreference):
    """
    Dynamic preference to store the number of peridos that is too long a gap
    between running tasks that are not controlled by celery

    :access_key: 'commonalertargs__external_task_every'
    """
    section = COMMON_ALERT_ARGS
    name = 'external_task_every'
    default = 10
    required = True
    verbose_name = _('The expected longest wait between instances of events '
                     'whose period is set externally (to the django app).').title()


def get_preference(key):
    """
    get the current value of a dynamic preference
    (also known as a dynamic setting)

    :arg str key: the accessor key for the preference
        it follows this format 'section__preference_name`
    """
    section, name = key.split('__')
    # TODO figure out how to get the cache working properly, instead of doing
    #      this weird workaround
    db_pref = global_preferences_registry.manager().get_db_pref(section, name)

    return db_pref.value


def get_list_preference(key):
    """
    get the a list from a dynamic preference
    (also known as a dynamic setting)

    :arg str key: the accessor key for the preference
        it follows this format 'section__preference_name`
    """
    return get_preference(key).split(',')


def get_int_list_preference(key):
    """
    get a list of ints from a dynamic preference


    :arg str key: the accessor key for the preference
        it follows this format 'section__preference_name`
    :return list: returns the list of integers represented by the string
                  preference
    """
    return [int(i) for i in get_list_preference(key)]
