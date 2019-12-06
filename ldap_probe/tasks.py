"""
ldap_probe.tasks
-----------------

This module contains the `Celery tasks
<https://docs.celeryproject.org/en/latest/userguide/tasks.html>`__
used by the :ref:`Domain Controllers Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:contact:    daniel.busto@phsa.ca

:updated:    Nov. 19, 2019

"""
from celery import shared_task, group
from celery.utils.log import get_task_logger

from ldap_probe import ad_probe, models, exceptions
from citrus_borg.dynamic_preferences_registry import get_preference
from p_soc_auto_base import utils

LOG = get_task_logger(__name__)
"""default :class:`logger.Logging` instance for this module"""


@shared_task(queue='ldap_probe', rate_limit='5/s')
def probe_ad_controller(ad_model=None, ad_pk=None, logger=LOG):
    """
    probe the domain and save the AD monitoring data

    :arg str ad_model: the specification for the
        :class:`django.db. models.Model` containing the `AD` specification

    :arg int ad_pk: the primary key of the
        :class:`django.db.modles.Model` instance that contains the
        AD controller  node information

    :arg logger: the logger instance
    :type logger: :class:`loggingLogger`

    :returns: the return of
        :meth:`ldap_probe.models.LdapProbeLog.create_from_probe`

    :raises: :exc:`exceptions.Exception`
    """
    try:
        ad_model = utils.get_model(ad_model)
    except utils.UnknownDataTargetError as error:
        raise error

    if not isinstance(ad_pk, int):
        raise TypeError(f'Bad dog! No {type(ad_pk)} type biscuit for you')

    try:
        created = models.LdapProbeLog.create_from_probe(
            ad_probe.ADProbe.probe(ad_model.objects.get(pk=ad_pk))
        )
    except Exception as error:
        logger.error(error)
        raise error

    logger.debug(created)

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

        This item in this argument must be represented using the
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

    results = []
    for data_source in data_sources:
        pk_list = utils.get_pk_list(
            utils.get_base_queryset(data_source, enabled=True))
        group(probe_ad_controller.s(data_source, ad_pk) for ad_pk in pk_list)()
        results.append(
            f'Will probe {len(pk_list)} AD controllers from {data_source}.')

    return '\n'.join(results)


@shared_task(queue='data_prune')
def expire_entries(data_source=None, **age):
    """
    mark row in the :class:`model <django.db.models.Model>` defined by
    the data_source argument as expired if they were created before a
    specific date and time

    The assumption is that the :class:`model <django.db.models.Model>`
    defined by the data_source argument has a field named `created_on`
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

        :exc:`p_soc-auto.base.utils.UnknownDataTargetError` if the
        `data_source` argument cannot be resolved to a valid
        :class:`django.db.models.Model`

        :exc:`exceptions.AttributeError` if the
            :class:`django.db.models.Model` resolved from the `data_source`
            argument doesn't have both a `created_on` attribute and an
            `is_expired` attribute

    """
    if data_source is None:
        data_source = 'ldap_probe.LdapProbeLog'

    try:
        data_source = utils.get_model(data_source)
    except utils.UnknownDataTargetError as error:
        raise error

    if not hasattr(data_source, 'created_on'):
        raise AttributeError(
            f'Cannot do age tracking in the {data_source._meta.model_name}.'
            ' It does not have a created_on field')

    if not hasattr(data_source, 'is_expired'):
        raise AttributeError(
            f'Cannot expire rows in the {data_source._meta.model_name}.'
            ' It does not have an is_expired field')

    if not age:
        older_than = utils.MomentOfTime.past(
            time_delta=get_preference('ldapprobe__ldap_expire_after'))
    else:
        older_than = utils.MomentOfTime.past(**age)

    count_expired = data_source.objects.filter(created_on__lte=older_than).\
        update(is_expired=True)

    # pylint: disable=protected-access
    return (
        f'Marked {count_expired} {data_source._meta.verbose_name} rows'
        f' created earlier than {older_than:%B %d, %Y at %H:%M} as expired.'
    )
    # pylint: enable=protected-access


@shared_task(queue='data_prune')
def delete_expired_entries(data_source=None):
    """
    delete rows marked as expired from the :class:`model
    <django.db.models.Model>` defined by the data_source argument

    This task assumes that the :class:`model <django.db.models.Model>`
    defined by the data_source argument has a :class:`bool` attribute named
    `is_expred`.

    The task will actually delete entries only if the


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
    if not get_preference('ldapprobe__ldap_delete_expired'):
        return 'the application is not configured to delete expired rows'

    if data_source is None:
        data_source = 'ldap_probe.LdapProbeLog'

    try:
        data_source = utils.get_model(data_source)
    except utils.UnknownDataTargetError as error:
        raise error

    if not hasattr(data_source, 'is_expired'):
        raise AttributeError(
            f'There are no expired rows in the'
            f' {data_source._meta.model_name}.'
            ' It does not have an is_expired field')

    count_deleted = data_source.objects.filter(is_expired=True).all().delete()

    return (
        f'Deleted {count_deleted} expired rows from'
        f' {data_source._meta.verbose_name}'
    )


@shared_task(queue='data_prune')
def trim_ad_duplicates():
    """
    this function makes sure that if the definition for an `AD` node is
    present in both :class:`ldap_probe.models.OrionADNode` and
    :class;`ldap_probe.models.NonOrionADNode`, the later will be deleted

    The advantage of considering the `AD` definitions in
    :class:`ldap_probe.models.OrionADNode` to be the `truthy` ones is
    that the data in that particular model is maintained automatically
    as far as our application is concerned
    """
    for node in utils.get_model('ldap_probe.nonorionadnode').objects.all():
        try:
            node.remove_if_in_orion(logger=LOG)
        except Exception as error:
            LOG.error(error)
            raise error


@shared_task(queue='email', rate_limit='1/s')
def raise_ldap_probe_failed_alert(instance_pk=None, subscription=None):
    """
    raise an email alert for a failed instance of the
    :class:`ldap_probe.models.LdapProbeLog` model

    :arg int instance_pk: the primary key of the instance

    :arg str subscription: the value of the :attr:`subscription
        <ssl_cert_tracker.models.Subscription.subscription>` attribute
        used to retrieve the
        :class:`ssl_cert_tracker.models.Subscription` instance required
        for raising this alert via email

    """
    if subscription is None:
        subscription = get_preference('ldapprobe__ldap_error_subscription')

    return _raise_ldap_alert(
        instance_pk=instance_pk,
        subscription=utils.get_subscription(subscription),
        level=get_preference('commonalertargs__error_level'))


@shared_task(queue='email', rate_limit='1/s')
def raise_ldap_probe_perf_alert(instance_pk=None, subscription=None):
    """
    raise an email alert for an instance of the
    :class:`ldap_probe.models.LdapProbeLog` model that shows performance
    error problems

    :arg int instance_pk: the primary key of the instance

    :arg str subscription: the value of the :attr:`subscription
        <ssl_cert_tracker.models.Subscription.subscription>` attribute
        used to retrieve the
        :class:`ssl_cert_tracker.models.Subscription` instance required
        for raising this alert via email

    """
    if subscription is None:
        subscription = get_preference('ldapprobe__ldap_perf_subscription')

    return _raise_ldap_alert(
        instance_pk=instance_pk,
        subscription=utils.get_subscription(subscription),
        level=get_preference('commonalertargs__error_level'))


@shared_task(queue='email', rate_limit='1/s')
def raise_ldap_probe_perf_warn(instance_pk=None, subscription=None):
    """
    raise an email alert for an instance of the
    :class:`ldap_probe.models.LdapProbeLog` model that shows performance
    warning problems

    :arg int instance_pk: the primary key of the instance

    :arg str subscription: the value of the :attr:`subscription
        <ssl_cert_tracker.models.Subscription.subscription>` attribute
        used to retrieve the
        :class:`ssl_cert_tracker.models.Subscription` instance required
        for raising this alert via email

    """
    if subscription is None:
        subscription = get_preference('ldapprobe__ldap_perf_subscription')

    return _raise_ldap_alert(
        instance_pk=instance_pk,
        subscription=utils.get_subscription(subscription),
        level=get_preference('commonalertargs__warn_level'))


@shared_task(queue='email', rate_limit='1/s')
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

    :arg time_delta_args: optional named arguments that are used to
            initialize a :class:`datetime.duration` object

            If not present, the method will use the period defined by the
            :class:`citrus_borg.dynamic_preferences_registry.LdapReportPeriod`
            user preference
    """
    LOG.debug(
        ('invoking ldap probes report with data_source = %s, anon = %s,'
         ' perf_filter = %s, time_delta_args = %s'),
        data_source, anon, perf_filter, time_delta_args)
    try:
        now, time_delta, subscription, data, perf_filter = \
            utils.get_model(data_source).\
            report_probe_aggregates(
                anon=anon, perf_filter=perf_filter, **time_delta_args)
    except Exception as error:
        LOG.error(
            ('invoking ldap probes report with data_source = %s, anon = %s,'
             ' perf_filter = %s, time_delta_args = %s raises error %s'),
            data_source, anon, perf_filter, time_delta_args, str(error))
        raise error

    subscription = utils.get_subscription(subscription)
    full = 'full bind' in subscription.subscription.lower()
    orion = 'non orion' not in subscription.subscription.lower()

    try:
        ret = utils.borgs_are_hailing(
            data=data, subscription=subscription, logger=LOG,
            level=get_preference('commonalertargs__info_level'), now=now,
            time_delta=time_delta, full=full, orion=orion,
            perf_filter=perf_filter)
    except Exception as error:
        raise error

    if ret:
        return (
            f'dispatched LDAP probes report with data_source = {data_source},'
            f' anon = {anon}, perf_filter = {perf_filter},'
            f' time_delta_args = {time_delta_args}')

    return (
        f'could not dispatch LDAP probes report with'
        f' data_source = {data_source},'
        f' anon = {anon}, perf_filter = {perf_filter},'
        f' time_delta_args = {time_delta_args}')


def _raise_ldap_alert(subscription, level, instance_pk=None):
    """
    invoke the email sending mechanism for an `LDAP` alert

    This is an unusual usage for :class:`ssl_cert_tracker.lib.Email`.
    The data is not exactly tabular and most of the email data must be
    provided using :attr:`ssl_cert_tracker.lib.Email.extra_context`
    because it is not generated at the database level but at the `Python`
    level.

    :arg data: the data required for populating the email object
    :type data: :class:`django.db.models.query.QuerySet`

    :arg subscription: the subscription required for addressing and
        rendering the email object
    :type subscription: :class:`ssl_cert_tracker.models.Subscription`

    :arg logger: the logger instance
    :type logger: :class:`logging.Logger`

    :arg str level: the level of the alert

    :arg ldap_probe: the :class:`ldap_probe.models.LdapProbeLog` instance
        that is subject to the alert

    :returns: an interpretation of the return value of the
        :meth:`ssl_cert_trqcker.lib.Email.send` operation

    :raises: generic :exc:`exceptions.Exception` for whatever error is
        raised by :meth:`ssl_cert_trqcker.lib.Email.send`
    """
    if instance_pk is None:
        raise exceptions.AlertArgsError(
            'Must provide LDAP probe identifier when raising this alert')

    data = utils.get_model('ldap_probe.ldapprobelog').objects.filter(
        id=instance_pk)

    ldap_probe = data.get()

    try:
        ret = utils.borgs_are_hailing(
            data=data, subscription=subscription, logger=LOG,
            add_csv=False, level=level, node=ldap_probe.node,
            created_on=ldap_probe.created_on,
            probe_url=ldap_probe.absolute_url,
            orion_url=ldap_probe.ad_node_orion_url)
    except Exception as error:
        raise error

    if ldap_probe.failed:
        return_specification = 'error alert for'

    elif ldap_probe.perf_alert:
        return_specification = 'performance alert for'

    else:
        return_specification = 'performance warning for'

    if not ret:
        return f'could not raise {return_specification} {ldap_probe}'

    return f'raised {return_specification} {ldap_probe}'
