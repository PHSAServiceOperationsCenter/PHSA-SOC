"""
ldap_probe.tasks
-----------------

This module contains the `Celery tasks
<https://docs.celeryproject.org/en/latest/userguide/tasks.html>`__
used by the :ref:`Active Directory Services Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from smtplib import SMTPConnectError

from celery import shared_task, group
from celery.utils.log import get_task_logger
from django.apps import apps
from django.utils import timezone

from citrus_borg.dynamic_preferences_registry import get_preference
from ldap_probe.ad_probe import ADProbe
from ldap_probe.ldap_probe_log import LdapProbeLog
from p_soc_auto_base import utils
from p_soc_auto_base.utils import get_absolute_admin_change_url, \
    get_or_create_user
from p_soc_auto_base.email import Email
from p_soc_auto_base.models import DeletionLog, Subscription

LOG = get_task_logger(__name__)
"""default :class:`logger.Logging` instance for this module"""


@shared_task(queue='ldap_probe', rate_limit='5/s')
def probe_ad_controller(ad_model, ad_pk):
    """
    probe the domain and save the AD monitoring data

    :arg str ad_model: the specification for the
        :class:`django.db. models.Model` containing the `AD` specification

    :arg int ad_pk: the primary key of the
        :class:`django.db.modles.Model` instance that contains the
        AD controller  node information

    :returns: the return of
        :meth:`ldap_probe.models.LdapProbeLog.create_from_probe`

    :raises: :exc:`TypeError` if ad_pk is not an integer.
    """
    # TODO handle this error more gracefully
    try:
        ad_model = apps.get_model(ad_model)
    except utils.UnknownDataTargetError as error:
        raise error

    if not isinstance(ad_pk, int):
        raise TypeError(f'ad_pk must be an integer. Got: {type(ad_pk)}.')

    try:
        created = LdapProbeLog.create_from_probe(
            ADProbe.probe(ad_model.objects.get(pk=ad_pk))
        )
    except Exception as error:
        LOG.exception(error)
        raise error

    return created


@shared_task(queue='ldap_probe')
def bootstrap_ad_probes(data_sources=None):
    """
    launch a separate probing task for each `AD` controller extracted
    from the arguments

    This task uses the `Celery Canvas Group primitive
    <https://docs.celeryproject.org/en/latest/userguide/canvas.html#groups>`__
    to launch multiple parallel instances of the :meth:`probe_ad_controller`
    task.

    :arg data_sources: the name(s) of the :class:`Django model(s)
        <django.db.models.Model>` that store `AD` controller information

        This item in the argument must be represented using the
        `app_label.model_name` convention. The argument can be a
        :class:`list` or a :class:`tuple`, or a :class:`str` that separates
        each entry using a comma (,) character.

        By default this argument points to the models defined under
        :class:`ldap_probe.models.OrionADNode` and
        :class:`ldap_probe.models.NonOrionADNode`

    :returns: a `CR` separated string containing the name of each data
        source and the number of `AD` controllers defined under said source
    :rtype: str
    """
    if data_sources is None:
        data_sources = 'ldap_probe.OrionADNode,ldap_probe.NonOrionADNode'

    if not isinstance(data_sources, (list, tuple)):
        data_sources = data_sources.split(',')

    for data_source in data_sources:
        pk_list = utils.get_pk_list(
            utils.get_base_queryset(data_source, enabled=True))
        group(probe_ad_controller.s(data_source, ad_pk) for ad_pk in pk_list)()
        LOG.info('Will probe %s AD controllers from %s.', len(pk_list),
                 data_source)


@shared_task(queue='data_prune')
def expire_entries(data_source=None, **age):
    """
    mark rows in the :class:`model <django.db.models.Model>` defined by
    the data_source argument as expired if they were created before a
    specific date and time

    The assumption is that the :class:`model <django.db.models.Model>`
    defined by the data_source argument has a field named `created`
    and a field named `is_expired`.

    :arg str data_source: the name of a :class:`model
        <django.db.models.Model>` in the `app_label.modelname` format

        By default this argument will point to the
        :class:`ldap_probe.models.LdapProbeLog` model

    :arg age: named arguments that can be used for creating a
        :class:`datetime.timedelta` object

        See `Python docs for timedelta objects
        <https://docs.python.org/3.6/library/datetime.html#timedelta-objects>`__

    :returns: the name of the data source, the number of rows affected and
        the date and time used for choosing the rows

    :raises:

        :exc:`p_soc_auto.base.utils.UnknownDataTargetError` if the
        `data_source` argument cannot be resolved to a valid
        :class:`django.db.models.Model`

        :exc:`AttributeError` if the
            :class:`django.db.models.Model` resolved from the `data_source`
            argument doesn't have both a `created` attribute and an
            `is_expired` attribute

    """
    LOG.info('kicked expire_entries')
    if data_source is None:
        data_source = 'ldap_probe.LdapProbeLog'

    try:
        data_source = apps.get_model(data_source)
    except utils.UnknownDataTargetError as error:
        raise error

    if not hasattr(data_source, 'created'):
        raise AttributeError(
            f'Cannot do age tracking in the {data_source._meta.model_name}.'
            ' It does not have a created field')

    if not hasattr(data_source, 'is_expired'):
        raise AttributeError(
            f'Cannot expire rows in the {data_source._meta.model_name}.'
            ' It does not have an is_expired field')

    if not age:
        older_than = utils.MomentOfTime.past(
            time_delta=get_preference('ldapprobe__ldap_expire_after'))
    else:
        older_than = utils.MomentOfTime.past(**age)

    count_expired = data_source.objects.filter(created__lte=older_than).\
        update(is_expired=True)

    LOG.info('Marked %s %s rows created earlier than %s as expired.',
             count_expired, data_source._meta.verbose_name,
             older_than.isoformat())


@shared_task(queue='data_prune')
def delete_expired_entries(data_source=None):
    """
    delete rows marked as expired from the :class:`model
    <django.db.models.Model>` defined by the `data_source` argument

    This task assumes that the :class:`model <django.db.models.Model>`
    defined by the data_source argument has a :class:`bool` attribute named
    `is_expired`.

    The task will actually delete entries only if the user preference defined
    in :class:
    `citrus_borg.dynamic_preferences_registry.LdapDeleteExpiredProbeLogEntries`
    is so configured.

    :arg str data_source: the name of a :class:`model
        <django.db.models.Model>` in the `app_label.modelname` format

        By default this argument will point to the
        :class:`ldap_probe.models.LdapProbeLog` model

    :returns: the name of the data source and the number of deleted rows

    :raises:

        :exc:`p_soc-auto.base.utils.UnknownDataTargetError` if the
        `data_source` argument cannot be resolved to a valid
        :class:`django.db.models.Model`

        :exc:`exceptions.AttributeError` if the
        :class:`django.db.models.Model` resolved from the `data_source`
        argument doesn't have an `is_expired` attribute

    """
    LOG.debug('kick delete_expired_entries')
    if not get_preference('ldapprobe__ldap_delete_expired'):
        LOG.info('the application is not configured to delete expired rows')
        return

    if data_source is None:
        data_source = 'ldap_probe.LdapProbeLog'

    try:
        data_source = apps.get_model(data_source)
    except utils.UnknownDataTargetError:
        LOG.exception('Cannot delete entries for non-existent model %s',
                      data_source)
        raise

    if not hasattr(data_source, 'is_expired'):
        raise AttributeError(
            f'There are no expired rows in {data_source._meta.model_name}.'
            ' It does not have an is_expired field')

    count_deleted = data_source.objects.filter(is_expired=True).all().delete()

    DeletionLog(model_name=str(data_source), records_deleted=count_deleted[0]).save()

    LOG.info('Deleted %s expired rows from %s',
             count_deleted, data_source._meta.verbose_name)


@shared_task(queue='data_prune')
def trim_ad_duplicates():
    """
    this function makes sure that if the definition for an `AD` node is
    present in both :class:`ldap_probe.models.OrionADNode` and
    :class:`ldap_probe.models.NonOrionADNode`, the later will be deleted

    The advantage of considering the `AD` definitions in
    :class:`ldap_probe.models.OrionADNode` to be the `truthy` ones is
    that the data in that particular model is maintained automatically
    as far as our application is concerned

    :raises: :exc:`Exception` so that the exception is passed to `Celery`
    """
    for node in apps.get_model('ldap_probe.nonorionadnode').objects.all():
        node.remove_if_in_orion()


@shared_task(queue='data_prune')
def maintain_ad_orion_nodes():
    """
    synchronize :class:`ldap_probe.models.OrionADNode` with
    :class:`orion_integration.models.OrionDomainControllerNode`

    This is needed because `AD` `Orion` nodes may change outside this
    application
    """
    known_nodes_model = apps.get_model('ldap_probe.orionadnode')
    new_nodes_model = apps.get_model(
        'orion_integration.oriondomaincontrollernode')

    known_node_ids = known_nodes_model.objects.values_list(
        'node_id', flat=True)

    new_nodes = new_nodes_model.objects.exclude(id__in=known_node_ids)

    if not new_nodes.exists():
        LOG.debug('did not find any unknown AD nodes in Orion')
        return

    service_user = get_or_create_user(
        name=get_preference('ldapprobe__service_user'))
    ldap_bind_cred = apps.get_model('ldap_probe.ldapbindcred').default()

    for node in new_nodes:
        new_ad_orion_node = known_nodes_model(
            node=node, ldap_bind_cred=ldap_bind_cred,
            created_by=service_user, updated_by=service_user)
        try:
            new_ad_orion_node.save()
        except Exception as error:
            LOG.exception(error)
            raise error

    LOG.info('created %s AD nodes from Orion', new_nodes.count())


@shared_task(queue='email', rate_limit='1/s')
def raise_ldap_probe_failed_alert(instance_pk=None, subscription=None):
    """
    raise an email alert for a failed instance of the
    :class:`ldap_probe.models.LdapProbeLog` model

    :arg int instance_pk: the primary key of the instance

    :arg str subscription: the value of the :attr:`subscription
        <p_soc_auto_base.models.Subscription.subscription>` attribute
        used to retrieve the
        :class:`p_soc_auto_base.models.Subscription` instance required
        for raising this alert via email

    """
    if subscription is None:
        subscription = get_preference('ldapprobe__ldap_error_subscription')

    return _raise_ldap_alert(
        instance_pk=instance_pk,
        subscription=Subscription.get_subscription(subscription),
        level=get_preference('commonalertargs__error_level'))


@shared_task(queue='email', rate_limit='1/s')
def raise_ldap_probe_perf_err(instance_pk=None, subscription=None):
    """
    raise an email alert for an instance of the
    :class:`ldap_probe.models.LdapProbeLog` model that shows performance
    'never exceed' problems

    :arg int instance_pk: the primary key of the instance

    :arg str subscription: the value of the :attr:`subscription
        <p_soc_auto_base.models.Subscription.subscription>` attribute
        used to retrieve the
        :class:`p_soc_auto_base.models.Subscription` instance required
        for raising this alert via email

    """
    if subscription is None:
        subscription = get_preference('ldapprobe__ldap_perf_subscription')

    return _raise_ldap_alert(
        instance_pk=instance_pk,
        subscription=Subscription.get_subscription(subscription),
        level=get_preference('commonalertargs__error_level'))


@shared_task(queue='email', rate_limit='1/s')
def raise_ldap_probe_perf_alert(instance_pk=None, subscription=None):
    """
    raise an email alert for an instance of the
    :class:`ldap_probe.models.LdapProbeLog` model that shows performance
    error problems

    :arg int instance_pk: the primary key of the instance

    :arg str subscription: the value of the :attr:`subscription
        <p_soc_auto_base.models.Subscription.subscription>` attribute
        used to retrieve the
        :class:`p_soc_auto_base.models.Subscription` instance required
        for raising this alert via email

    """
    if subscription is None:
        subscription = get_preference('ldapprobe__ldap_perf_subscription')

    return _raise_ldap_alert(
        instance_pk=instance_pk,
        subscription=Subscription.get_subscription(subscription),
        level=get_preference('commonalertargs__warn_level'))


@shared_task(queue='email', rate_limit='1/s')
def raise_ldap_probe_perf_warn(instance_pk=None, subscription=None):
    """
    raise an email alert for an instance of the
    :class:`ldap_probe.models.LdapProbeLog` model that shows performance
    warning problems

    :arg int instance_pk: the primary key of the instance

    :arg str subscription: the value of the :attr:`subscription
        <p_soc_auto_base.models.Subscription.subscription>` attribute
        used to retrieve the
        :class:`p_soc_auto_base.models.Subscription` instance required
        for raising this alert via email

    """
    if subscription is None:
        subscription = get_preference('ldapprobe__ldap_perf_subscription')

    return _raise_ldap_alert(
        instance_pk=instance_pk,
        subscription=Subscription.get_subscription(subscription),
        level=get_preference('commonalertargs__info_level'))


@shared_task(queue='email', rate_limit='1/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def dispatch_bad_fqdn_reports():
    """
    `Celery task` for generating a report with `AD` nodes with no `FQDN`
    properties on the `Orion` server

    :returns: a :class:`str` object interpreting the `return` of
        :meth:`ssl_cert_tracker.lib.Email.send`

    """
    LOG.debug('invoking the fqdn report for orion ad nodes')

    try:
        data = apps.get_model('ldap_probe.orionadnode').report_bad_fqdn()
    except Exception as error:
        LOG.exception(
            'invoking the fqdn report for orion ad nodes raises error %s',
            str(error))
        raise error

    subscription = Subscription.get_subscription(
        get_preference('ldapprobe__ldap_orion_fqdn_ad_nodes_subscription'))

    info_level = get_preference('commonalertargs__info_level')

    if Email.send_email(data=data, subscription=subscription,
                        level=info_level):
        LOG.info('dispatched the fqdn report for orion ad nodes')
        return

    LOG.warning('could not dispatch the fqdn report for orion ad nodes')


@shared_task(queue='email', rate_limit='1/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def dispatch_dupe_nodes_reports():
    """
    `Celery task` for generating a report with duplicate `AD` nodes
    on the `Orion` server

    :returns: a :class:`str` object interpreting the `return` of
        :meth:`ssl_cert_tracker.lib.Email.send`

    """
    LOG.debug('invoking the duplicate ad nodes in orion report')

    try:
        data = apps.get_model('ldap_probe.orionadnode').\
            report_duplicate_nodes()
    except Exception as error:
        LOG.exception('invoking the duplicate ad nodes in orion report raises'
                      ' error %s', str(error))
        raise error

    subscription = Subscription.get_subscription(
        get_preference('ldapprobe__ldap_orion_dupes_ad_nodes_subscription'))

    info_level = get_preference('commonalertargs__info_level')

    if Email.send_email(data=data, subscription=subscription,
                        level=info_level):
        LOG.info('dispatched the duplicate ad nodes in orion report')
        return

    LOG.warning('could not dispatch the duplicate ad nodes in orion report')


@shared_task(queue='email', rate_limit='1/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def dispatch_non_orion_ad_nodes_report():
    """
    `Celery task` for generating the report about `AD` network nodes
    not defined in `Orion`

    :returns: information about the arguments used to call the task and the
        result of :meth:`ssl_cert_tracker.lib.Email.send`
    :rtype: str

    :raises: :exc:`Exception` to allow `Celery` to deal with
        errors

    """
    LOG.debug('invoking the non orion ad nodes report')

    try:
        data = apps.get_model('ldap_probe.nonorionadnode').active
    except Exception as error:
        LOG.exception('invoking the non orion ad nodes report raises error %s',
                      str(error))
        raise error

    subscription = Subscription.get_subscription(
        get_preference('ldapprobe__ldap_non_orion_ad_nodes_subscription'))

    warn_level = get_preference('commonalertargs__warn_level')
    if Email.send_email(data=data, subscription=subscription, level=warn_level):
        LOG.info('dispatched the non orion ad nodes report')
        return

    LOG.warning('could not dispatch the non orion ad nodes report')


@shared_task(queue='email', rate_limit='1/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def dispatch_ldap_error_report(**time_delta_args):
    """
    `Celery task` for generating `AD` services monitoring error reports

    :arg time_delta_args: optional named arguments that are used to
            initialize a :class:`datetime.duration` object

            If not present, the method will use the period defined by the
            :class:`citrus_borg.dynamic_preferences_registry.LdapReportPeriod`
            user preference
    :returns: information about the arguments used to call the task and the
        result of :meth:`ssl_cert_tracker.lib.Email.send`
    :rtype: str

    :raises: :exc:`Exception` to allow `Celery` to deal with
        errors

    """
    LOG.debug(
        'invoking ldap error report with time_delta_args: %s',
        time_delta_args)

    if time_delta_args:
        time_delta = timezone.timedelta(**time_delta_args)
    else:
        time_delta = get_preference('ldapprobe__ldap_reports_period')

    now = timezone.now()

    try:
        data = apps.get_model('ldap_probe.ldapprobelog').\
            error_report(time_delta)
    except Exception as error:
        LOG.exception(
            ('invoking ldap error report with time_delta_args: %s'
             ' raises error %s'), time_delta_args, error)
        raise error

    subscription = Subscription.get_subscription(
        get_preference('ldapprobe__ldap_error_report_subscription'))

    error_level = get_preference('commonalertargs__error_level')

    if Email.send_email(data=data, subscription=subscription, level=error_level,
                        now=now, time_delta=time_delta):
        LOG.info('dispatched LDAP error report with time_delta_args: %s',
                 time_delta_args)
        return

    LOG.warning('could not dispatch LDAP error report with time_delta_args: %s',
                time_delta_args)


@shared_task(queue='email')
def dispatch_ldap_perf_reports(
        data_sources=None, levels=None, buckets=None, **time_delta_args):
    """
    launch the tasks responsible for the performance degradation reports

    The number of performance degradation reports is determined by:

    * the performance buckets that we are tracking: these are instances"""\
    """of the :class:`ldap_probe.models.ADNodePerfBucket` model

    * the `AD` nodes that we are tracking: known to Orion or not known to Orion

    * the performance degradation levels that we are tracking: these are
      defined by the user preference classes belonging to the
      :attr:`citrus_borg.dynamic_preferences_registry.common_alert_args`
      :class:`Section <dynamic_preferences.preferences.Section>`,
      specifically the ones dealing with levels

    By default, this task will use all the possible combinations so that all
    the possible performance degradation reports will be dispatched but it
    is possible to specify exactly which report one desires to generate by
    way of using the arguments used by this task.
    It is also possible to launch multiple instances of this task, each
    instance dealing with a specific group of performance degradation reports.
    In either case, reports for both full bind probes and anonymous bind probes
    will be generated.

    :arg data_sources: the data sources containing the `AD` nodes

        This argument can be a :class:`list` or a :class:`str` containing
        the names of the models with `AD` node information using the
        'app_label.model_name' convention. When using the :class:`str`
        format, the model names must be separated by the ',' (comma)
        character.

        When not specified, the task will use nodes from both
        :class:`ldap_probe.models.OrionADNode` and
        :class:`ldap_probe.models.NonOrionADNode` models.

    :arg levels: the performance degradation levels

        This argument can be a :class:`list`, or a :class:`str` using
        commas (',') to separate the levels.

        The level must match the entries under the user preferences level
        classes that are part of the
        :attr:`citrus_borg.dynamic_preferences_registry.common_alert_args`
        :class:`Section <dynamic_preferences.preferences.Section>` as follows:

        * INFO: will measure performance degradation against the threshold
          defined by the value of the
          :attr:`ldap_probe.models.ADNodePerfBucket.avg_warn_threshold`
          attribute of the :class:`ldap_probe.models.ADNodePerfBucket` instance
          to which the `AD` node belongs

        * WARNING: uses the value of the
          :attr:`ldap_probe.models.ADNodePerfBucket.avg_err_threshold`

        * ERROR: uses the value of the
          :attr:`ldap_probe.models.ADNodePerfBucket.alert_threshold`

        If not specified, performance degradation reports for all 3 levels
        will be generated.

    :arg buckets: the performance buckets

        This argument can be a :class:`list`, or a :class:`str` using
        commas (',') to separate the levels.

        Each bucket must match an entry in the
        :attr:`ldap_probe.models.ADNodePerfBucket.performance_bucket` column.

        If not specified, performance degradation reports for all `enabled`
        buckets will be generated.

    :arg time_delta_args: optional named arguments that are used to
            initialize a :class:`datetime.timedelta` object

            If not present, the method will use the period defined by the
            :class:`citrus_borg.dynamic_preferences_registry.LdapReportPeriod`
            user preference

    :returns: information about the arguments used to invoke the tasks
    """
    if data_sources is None:
        data_sources = ['ldap_probe.OrionADNode', 'ldap_probe.NonOrionADNode']

    if not isinstance(data_sources, (list, tuple)):
        data_sources = data_sources.split(',')

    if levels is None:
        levels = [get_preference('commonalertargs__error_level'),
                  get_preference('commonalertargs__warn_level'),
                  get_preference('commonalertargs__info_level'), ]

    if not isinstance(levels, (list, tuple)):
        levels = levels.split(',')

    if buckets is None:
        buckets = list(
            apps.get_model('ldap_probe.adnodeperfbucket').active.
            values_list('name', flat=True)
        )

    if not isinstance(buckets, (list, tuple)):
        buckets = buckets.split(',')

    LOG.info('bootstrapped performance reports, time_delta_args: %s',
             time_delta_args)
    LOG.info('buckets: %s', buckets)
    for data_source in data_sources:
        LOG.info('data_source: %s', data_source)
        for level in levels:
            LOG.info('level: %s', level)
            group(dispatch_ldap_perf_report.s(
                data_source=data_source, bucket=bucket, anon=True,
                level=level, **time_delta_args) for bucket in buckets)()
            group(dispatch_ldap_perf_report.s(
                data_source=data_source, bucket=bucket, anon=False,
                level=level, **time_delta_args) for bucket in buckets)()


@shared_task(queue='email', rate_limit='1/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def dispatch_ldap_perf_report(
        data_source, bucket, anon, level, **time_delta_args):
    """
    task that generates a performance degradation report via email for the
    arguments used to invoke it

    Under normal circumstances, this task will always be invoked via
    a `Celery group()
    <https://docs.celeryproject.org/en/latest/userguide/canvas.html#groups>`__
    call.

    :arg str data_source: the named of the model containing information
        about `AD` nodes using the 'app_lable.model_name' convention

    :arg str bucket: the value of the
        :attr:`ldap_probe.models.ADNodePerfBucket.performance_bucket` field;
        this will be used to retrieve the applicable thresholds from the
        :class:`ldap_probe.models.ADNodePerfBucket` instance

    :arg bool anon: look for full bind or anonymous bind probe data

    :arg str level: the performance degradation level

    :arg time_delta_args: optional named arguments that are used to
            initialize a :class:`datetime.timedelta` object

            If not present, the method will use the period defined by the
            :class:`citrus_borg.dynamic_preferences_registry.LdapReportPeriod`
            user preference

    :returns: information about the arguments used to call the task and the
        result of :meth:`ssl_cert_tracker.lib.Email.send`
    :rtype: str

    :raises:

        :exc:`Exception` if the data for the report cannot be generated of
        the email cannot be sent.

        If the send operation raises an :exc:`smtplib.SMTPConnectError`,
        the task execution will be retried up to 3 times before the
        exception is allowed to propagate.
    """
    LOG.debug(
        ('invoking ldap probes report with data_source: %s, bucket: %s,'
         ' anon: %s, level: %s, time_delta_args: %s'),
        data_source, bucket, anon, level, time_delta_args)

    try:
        (now, time_delta, subscription, data, threshold, no_nodes) = \
            apps.get_model(data_source).report_perf_degradation(
                bucket=bucket, anon=anon, level=level, **time_delta_args
                )
    except Exception as error:
        LOG.exception(
            ('invoking ldap probes report with data_source: %s,'
             ' bucket: %s, anon: %s, level: %s, time_delta_args: %s'
             ' raises error %s'),
            data_source, bucket, anon, level, time_delta_args, error)
        raise error

    if no_nodes:
        LOG.warning('there are no AD network nodes for %s', bucket)

    if not get_preference('ldapprobe__ldap_perf_send_good_news') and not data:
        LOG.info('there is no performance degradation for %s', bucket)
        return

    subscription = Subscription.get_subscription(subscription)
    full = 'full bind' in subscription.subscription.lower()
    orion = 'non orion' not in subscription.subscription.lower()
    threshold = utils.show_milliseconds(threshold)

    if Email.send_email(
            data=data, subscription=subscription, level=level, now=now,
            time_delta=time_delta, full=full, orion=orion, bucket=bucket,
            threshold=threshold):
        LOG.info('dispatched LDAP probes performance degradation report with '
                 'data_source: %s, anon: %s, bucket: %s, level: %s, '
                 'time_delta_args: %s',
                 data_source, anon, bucket, level, time_delta_args)
        return

    LOG.warning('could not dispatch LDAP probes performance degradation report'
                ' with data_source: %s, anon: %s, bucket: %s, level: %s,'
                ' time_delta_args: %s',
                data_source, anon, bucket, level, time_delta_args)


@shared_task(queue='email', rate_limit='1/s', max_retries=3,
             retry_backoff=True, autoretry_for=(SMTPConnectError,))
def dispatch_ldap_report(data_source, anon, perf_filter, **time_delta_args):
    """
    `Celery task` for generating `AD` services monitoring summary reports

    :arg str data_source: the name of the `Django model` to be used as a
        data source

        We are passing the model using its name because the default
        task serializer (`JSON`) is not capable of handling Python classes.
        If we use the name of the model, we can resolve the class inside
        the task.

    :arg bool anon: flag used to decide the type of the `AD` probes;
        probes that executed anonymous bind calls or probes that
        executed non anonymous bind calls

    :arg str perf_filter: apply filters for performance degradation if
            this argument is provided

            See :meth:`ldap_probe.models.BaseADNode.report_probe_aggregates`

    :arg time_delta_args: optional named arguments that are used to
            initialize a :class:`datetime.timedelta` object

            If not present, the method will use the period defined by the
            :class:`citrus_borg.dynamic_preferences_registry.LdapReportPeriod`
            user preference

    :returns: information about the arguments used to call the task and the
        result of :meth:`ssl_cert_tracker.lib.Email.send`
    :rtype: str

    """
    LOG.debug(
        ('invoking ldap probes report with data_source: %s, anon: %s,'
         ' perf_filter: %s, time_delta_args: %s'),
        data_source, anon, perf_filter, time_delta_args)
    try:
        # TODO why is report_probe_aggregates supplying now, time_delta, etc
        now, time_delta, subscription, data, perf_filter = \
            apps.get_model(data_source).\
            report_probe_aggregates(
                anon=anon, perf_filter=perf_filter, **time_delta_args)
    except Exception as error:
        LOG.exception(
            ('invoking ldap probes report with data_source: %s, anon: %s,'
             ' perf_filter: %s, time_delta_args: %s raises error %s'),
            data_source, anon, perf_filter, time_delta_args, str(error))
        raise error

    subscription = Subscription.get_subscription(subscription)
    full = 'full bind' in subscription.subscription.lower()
    orion = 'non orion' not in subscription.subscription.lower()

    if Email.send_email(
            data=data, subscription=subscription,
            level=get_preference('commonalertargs__info_level'), now=now,
            time_delta=time_delta, full=full, orion=orion,
            perf_filter=perf_filter):
        LOG.info('dispatched LDAP probes report with data_source: %s, anon: %s,'
                 ' perf_filter: %s, time_delta_args: %s',
                 anon, data_source, perf_filter, time_delta_args)
        return

    LOG.warning('could not dispatch LDAP probes report with data_source: %s,'
                ' anon: %s, perf_filter: %s, time_delta_args: %s',
                data_source, anon, perf_filter, time_delta_args)


def _raise_ldap_alert(subscription, level, instance_pk):
    """
    invoke the email sending mechanism for an `LDAP` alert

    This is an unusual usage for :class:`ssl_cert_tracker.lib.Email`.
    The data is not exactly tabular and most of the email data must be
    provided using :attr:`ssl_cert_tracker.lib.Email.extra_context` entries
    because it is not generated at the database level but at the `Python`
    level.

    :arg subscription: the subscription required for addressing and
        rendering the email object
    :type subscription: :class:`p_soc_auto_base.models.Subscription`

    :arg str level: the level of the alert

    :arg int instance_pk: the primary key of the
        :class:`ldap_probe.models.LdapProbeLog` that is subject to the alert

    :returns: an interpretation of the return value of the
        :meth:`ssl_cert_tracker.lib.Email.send` operation

    :raises: generic :exc:`exceptions.Exception` for whatever error is
        raised by :meth:`ssl_cert_tracker.lib.Email.send`
    """
    data = apps.get_model('ldap_probe.ldapprobelog').objects.filter(
        id=instance_pk)

    ldap_probe = data.get()

    if ldap_probe.ad_orion_node:
        change_url_args = {
            'admin_view': 'admin:ldap_probe_orionadnode_change',
            'obj_pk': ldap_probe.ad_orion_node.pk,
            'obj_anchor_name': str(ldap_probe.ad_orion_node)
        }
    else:
        change_url_args = {
            'admin_view': 'admin:ldap_probe_nonorionadnode_change',
            'obj_pk': ldap_probe.ad_node.pk,
            'obj_anchor_name': str(ldap_probe.ad_node)
        }

    try:
        ret = Email.send_email(
            data=data, subscription=subscription, add_csv=False,
            level=level, node=ldap_probe.node, errors=ldap_probe.errors,
            created=ldap_probe.created,
            probe_url=ldap_probe.absolute_url,
            orion_url=ldap_probe.ad_node_orion_url,
            # TODO why doesn't this have its own function?
            node_url=get_absolute_admin_change_url(**change_url_args),
            bucket=ldap_probe.node_perf_bucket.name,
            avg_warn_threshold=utils.show_milliseconds(
                ldap_probe.node_perf_bucket.avg_warn_threshold),
            avg_err_threshold=utils.show_milliseconds(
                ldap_probe.node_perf_bucket.avg_err_threshold),
            alert_threshold=utils.show_milliseconds(
                ldap_probe.node_perf_bucket.alert_threshold))
    except Exception as error:
        LOG.exception(error)
        raise error

    if ldap_probe.failed:
        return_specification = 'error alert for'

    elif ldap_probe.perf_alert:
        return_specification = 'performance alert for'

    else:
        return_specification = 'performance warning for'

    if not ret:
        LOG.error('could not raise %s %s', return_specification, ldap_probe)

    LOG.debug('raised %s %s', return_specification, ldap_probe)
