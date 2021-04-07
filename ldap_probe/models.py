"""
ldap_probe.models
-----------------

This module contains the :class:`django.db.models.Model` models for the
:ref:`Active Directory Services Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
import logging
import socket

from django.conf import settings
from django.core import validators
from django.db import models
from django.db.models import (
    Case, When, F, Value, TextField, URLField, Count, Avg, Min, Max, Q)
from django.db.models.functions import Concat
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from citrus_borg.preferences import get_preference
from p_soc_auto_base.models import BaseModel, BaseModelWithDefaultInstance
from p_soc_auto_base.utils import MomentOfTime


LOG = logging.getLogger(__name__)


def _get_default_ldap_search_base():
    return get_preference('ldapprobe__search_dn_default')


class LDAPBindCred(BaseModelWithDefaultInstance, models.Model):
    """
    :class:`django.db.models.Model` class used for storing credentials used
    for probing Windows domain controllers

    `LDAP Bind Credentials Set fields
    <../../../admin/doc/models/ldap_probe.ldapbindcred>`__
    """
    domain = models.CharField(
        _('windows domain'),
        max_length=15, db_index=True, blank=False, null=False,
        validators=[validators.validate_slug])
    username = models.CharField(
        _('domain username'),
        max_length=64, db_index=True, blank=False, null=False,
        validators=[validators.validate_slug])
    password = models.CharField(
        _('password'), max_length=64, blank=False, null=False)
    ldap_search_base = models.CharField(
        _('DN search base'), max_length=128, blank=False, null=False,
        default=_get_default_ldap_search_base)

    def __str__(self):
        return '%s\\%s' % (self.domain, self.username)

    class Meta:
        app_label = 'ldap_probe'
        constraints = [models.UniqueConstraint(
            fields=['domain', 'username'], name='unique_account')]
        indexes = [models.Index(fields=['domain', 'username'])]
        verbose_name = _('LDAP Bind Credentials Set')
        verbose_name_plural = _('LDAP Bind Credentials Sets')


def _get_default_alert_threshold():
    return get_preference('ldapprobe__ldap_perf_err')


def _get_default_warn_threshold():
    return get_preference('ldapprobe__ldap_perf_warn')


def _get_default_err_threshold():
    return get_preference('ldapprobe__ldap_perf_alert')


class ADNodePerfBucket(BaseModelWithDefaultInstance, models.Model):
    """
    :class:`django.db.models.Model` class used for storing acceptable
    performance data for AD monitoring

    `Performance Group for ADS Nodes fields
    <../../../admin/doc/models/ldap_probe.adnodeperfbucket>`__
    """

    name = models.CharField(
        _('Bucket name'), max_length=253, db_index=True, unique=True,
        help_text=_('A descriptive name to help determine which nodes should be'
                    ' included in the bucket.'))
    avg_warn_threshold = models.DecimalField(
        _('Warning Response Time Threshold'), max_digits=6,
        decimal_places=4, db_index=True, blank=False, null=False,
        default=_get_default_warn_threshold,
        help_text=_(
            'If the average AD services response time is worse than this'
            ' value, include this node in the periodic performance'
            ' degradation warnings report.'))
    avg_err_threshold = models.DecimalField(
        _('Error Response Time Threshold'), max_digits=6,
        decimal_places=4, db_index=True, blank=False, null=False,
        default=_get_default_err_threshold,
        help_text=_(
            'If the average AD services response time is worse than this'
            ' value, include this node in the periodic performance'
            ' degradation errors report.'))
    alert_threshold = models.DecimalField(
        _('Alert Response Time Threshold'), max_digits=6,
        decimal_places=4, db_index=True, blank=False, null=False,
        default=_get_default_alert_threshold,
        help_text=_(
            'If the AD services response time for any probe is worse than'
            ' this value, raise an immediate alert.'))

    def __str__(self):
        return self.name

    class Meta:
        app_label = 'ldap_probe'
        verbose_name = 'Performance Group for ADS Nodes'
        verbose_name_plural = 'Performance Groups for ADS Nodes'


class BaseADNode(BaseModel, models.Model):
    """
    `Django abstract model
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#abstract-base-classes>`__
    for storing information about `Windows` domain controller hosts
    """
    ldap_bind_cred = models.ForeignKey(
        'ldap_probe.LDAPBindCred', db_index=True, blank=False, null=False,
        default=LDAPBindCred.get_default, on_delete=models.PROTECT,
        verbose_name=_('LDAP Bind Credentials'))
    performance_bucket = models.ForeignKey(
        'ldap_probe.ADNodePerfBucket', db_index=True,
        default=ADNodePerfBucket.get_default,
        on_delete=models.SET_DEFAULT, verbose_name=_(
            'Acceptable Performance Limits'))

    sql_case_dns = When(
        ~Q(node__node_dns__iexact=''), then=F('node__node_dns'))
    """
    build an `SQL` `WHEN` clause

    See `Conditional Expressions
    <https://docs.djangoproject.com/en/2.2/ref/models/conditional-expressions/#the-conditional-expression-classes>`__.

    Observe the use of the `Q object
    <https://docs.djangoproject.com/en/2.2/topics/db/queries/#complex-lookups-with-q-objects>`__
    in the :class:`django.db.models.When`. We must use this construct because
    the value of the :attr:`orion_integration.models.OrionNode.node_dns`
    attribute (which is referenced from this model as `node__node_dns`) is
    never `null`; if not present, it can only be an empty string. As far
    as any database is concerned an empty string  is not the same as a
    `null` string and filtering from `Django` by `__isnull` will not have
    the desired effect here.
    """

    sql_orion_anchor_field = Case(
        sql_case_dns,
        default=F('node__ip_address'), output_field=TextField())
    """
    build an `SQL` `CASE` clause

    When used together with :attr:`sql_case_dns` this attribute allows us
    to append a meaningful field to a queryset. If
    :attr:`orion_integration.models.OrionNode.node_dns` exists, it will
    be placed in a :class:`django.db.models.query.QuerySet`. Otherwise,
    the :attr:`orion_integration.models.OrionNode.ip_address` will be
    used.

    """

    def get_node(self):
        """
        get node network information in either `FQDN` or `IP` address format

        We need this function mostly for retrieving node address information
        from `Orion` nodes. `Orion` nodes are guaranteed to have an `IP`
        address but sometimes they don't have a valid `FQDN`.
        """
        raise NotImplementedError()

    @classmethod
    def annotate_orion_url(cls, queryset=None):
        """
        `annotate
        <https://docs.djangoproject.com/en/2.2/topics/db/aggregation/>`__
        a :class:`queryset <django.db.models.query.QuerySet>` with the
        absolute `URL` of the node definition on the `Orion` server if
        possible or with a 'this node is not in orion' message

        The name of this annotation will be 'orion_url'.

        :arg queryset: a :class:`django.db.models.query.QuerySet` based
            on one of the models inheriting from :class:`BaseADNode`

            Default is the active nodes of the class.

        :returns: the values of the :class:`django.db.models.query.QuerySet`
            with the 'orion_url' field included
        """
        if queryset is None:
            queryset = cls.active

        queryset = cls._annotate_orion_url(queryset)

        return queryset.values()

    @classmethod
    def _annotate_orion_url(cls, queryset):
        """
        Helper method for :meth:`annotate_orion_url` that is overridden by the
        derived classes
        """
        raise NotImplementedError()

    @classmethod
    def annotate_probe_details(cls, probes_model_name, queryset=None):
        """
        annotate a :class:`queryset <django.db.models.query.QuerySet>`
        based on classes inheriting from :class:`BaseADNode` model with
        the absolute `URL` for the `Django admin summary' page with the
        `LDAP` probes executed against the AD node

        :Note:

            This method will be very expensive when invoked
            against a queryset that does not restrict the number of
            :class:`LdapProbeLog` rows.

        The annotation should look something like
        'http://lvmsocq01.healthbc.org:8091/admin/ldap_probe/"""\
        """ldapprobefullbindlog/?ad_node__isnull=True&"""\
        """ad_orion_node__id__exact=3388'.


        :arg str probes_model_name: determines the model name that will be
            used for generating the `URL`

            This is necessary because we are showing `LDAP` probes using
            separate models based on the type of the `AD` network node.

        :returns: a :class:`django.db.models.query.QuerySet` where each
            row (representing an `AD` node) includes a fields with the
            absolute `URL` for the results of the `LDAP` probes executed
            against the node

        """
        if queryset is None:
            queryset = cls.active

        return queryset.annotate(
            probes_url=Concat(
                Value(settings.SERVER_PROTO), Value('://'),
                Value(socket.getfqdn()), Value(':'),
                Value(settings.SERVER_PORT),
                Value('/admin/ldap_probe/'), Value(probes_model_name),
                Value(cls._details_url_filter()), F('id'),
                output_field=TextField())
        ).values()

    @classmethod
    def _details_url_filter(cls):
        raise NotImplementedError()

    @classmethod
    def report_perf_degradation(
            cls, bucket=None, anon=False, level=None, **time_delta_args):
        """
        generate report data for performance degradation reports

        This method invokes the :meth:`report_probe_aggregates` and then
        filters the results based on the performance thresholds defined
        for the :attr:`BaseADNode.performance_bucket`.

        In general tasks calling this method need to be invoked for each
        bucket.

        :arg bucket: the :class:`ADNodePerfBucket` instance;
            if not provided, the :class:`ADNodePerfBucket` default
            instance will be used

        :arg bool anon: are we looking at results from anonymous probes?

        :arg str level: this argument determines which threshold
            attribute of the :class:`ADNodePerfBucket` instance is used
            for comparison

            The decision is similar to log levels: `INFO` is using the
            smallest threshold, and `ERROR` is looking at the worst
            degradations. We are using this approach because the levels
            are defined via user preferences.

        :arg time_delta_args: optional named arguments that are used to
            initialize a :class:`datetime.timedelta` object

            If not present, the method will use the period defined by the
            :class:`citrus_borg.dynamic_preferences_registry.LdapReportPeriod`
            user preference

        :returns: a :class:`tuple` with the following fields:

            * the level used for determining the performace degradation
              filter

            * the primary key identifying the :class:`ADNodePerfBucket`
              instance

            * the moments used to filter the data in the report by time

            * the :attr:`subscription
              <p_soc_auto_base.models.Subscription.subscription>` that will
              be used to deliver this report via email

            * the :class:`django.db.models.query.QuerySet` based on one
              of the classes inheriting from  the :class:`BaseADNode` abstract
              model

        :raises:

            :exc:`ValueError` if a value is provided for the `bucket`
            argument that cannot be used for retrieving a
            :class:`ADNodePerfBucket` instance

            :exc:`TypError` if the default value of the bucket argument
            (`None`) is used and there is no default instance defined
            in :class:`ADNodePerfBucket`

            :exc:`ValueError` if the value of the `level` argument
            is not known to the system
        """
        if bucket is None:
            bucket = ADNodePerfBucket.default()
        else:
            try:
                bucket = ADNodePerfBucket.objects.get(name__iexact=bucket)
            except ADNodePerfBucket.DoesNotExist as error:
                raise ValueError(f'{bucket} does not exist: {str(error)}')

        now, time_delta, subscription, queryset, perf_filter \
            = cls.report_probe_aggregates(
                anon=anon, perf_filter=True, **time_delta_args)

        subscription = f'{subscription}, degrade'

        queryset = queryset.filter(performance_bucket=bucket)
        measure_point = 'average'

        if level == get_preference('commonalertargs__error_level'):
            subscription = f'{subscription}, err'
            measure_point = 'maximum'

        threshold = {
            None: bucket.avg_warn_threshold,
            get_preference('commonalertargs__info_level'):
                bucket.avg_warn_threshold,
            get_preference('commonalertargs__warn_level'):
                bucket.avg_err_threshold,
            get_preference('commonalertargs__error_level'):
                bucket.alert_threshold
        }[level]

        duration_filters = {
            'bind': {f'{measure_point}_bind_duration__gte': threshold},
            'read_root': {f'{measure_point}_read_root_dse_duration__gte':
                              threshold},
            'extended': {f'{measure_point}_extended_search_duration__gte':
                             threshold},
        }

        if anon:
            perf_filter = (Q(**duration_filters['bind'])
                           | Q(**duration_filters['read_root']))
        else:
            perf_filter = (Q(**duration_filters['bind'])
                           | Q(**duration_filters['extended']))

        # TODO figure out a better way to return all this stuff
        if not queryset.exists():
            return now, time_delta, subscription, queryset, threshold, True

        queryset = queryset.filter(perf_filter).values()

        return now, time_delta, subscription, queryset, threshold, False

    @classmethod
    def report_probe_aggregates(
            cls,
            queryset=None, anon=False, perf_filter=False, **time_delta_args):
        """
        generate report data with aggregate probe values for each instance of
        a class that inherits from :class:`BaseADNode` over the period defined
        by the `time_delta` argument

        :arg queryset: run the report against this particular queryset

            Normally, the queryset will be created by the method itself
            based on the class that owns it.
        :type queryset: :class:`django.db.models.query.QuerySet`

        :arg bool anon: flag for deciding which kind of LDAP probes are the
            subject of the report, LDAP probes that achieved a full bind or
            LDAP probes that achieved an anonymous bind

        :arg bool perf_filter: if `True`, the data generated here will be
            used for a performance degradtion report; this information is
            required in order to generate the proper subscription info

        :arg time_delta_args: optional named arguments that are used to
            initialize a :class:`datetime.timedelta` object

            If not present, the method will use the period defined by the
            :class:`citrus_borg.dynamic_preferences_registry.LdapReportPeriod`
            user preference

        :returns: a :class:`tuple` with the following fields:

            * the moments used to filter the data in the report by time

            * the :attr:`subscription
              <p_soc_auto_base.models.Subscription.subscription>` that will
              be used to deliver this report via email

            * the :class:`django.db.models.query.QuerySet` based on one
              of the classes inheriting from  the :class:`BaseADNode` abstract
              model

              Depending on the calling class the following aggregates with
              regards to LDAP probes are placed in the queryset

              * the number of failed probes

              * the number of successful probes

              * average timing for initialize calls of the successful probes

              * min, max, average timing for `bind` calls or `anonymous
                bind` calls of the successful probes

              * min, max, average timing for `extended search` calls or
                `read root dse` calls of the successful probes

        .. todo::

            Add a catch for no nodes available.

            This is a bad thing if there
            are no orion nodes (treat this case as a fully separate alert).

            However, the normal case is that all `AD` nodes are now
            defined in Orion and in that case, we can safely abort
            report calls for non Orion nodes.
        """
        subscription = 'LDAP: summary report'
        if queryset is None:
            queryset = cls.active

        if time_delta_args:
            time_delta = timezone.timedelta(**time_delta_args)
        else:
            time_delta = get_preference('ldapprobe__ldap_reports_period')

        since_moment = MomentOfTime.past(time_delta=time_delta)
        now = timezone.now()

        if anon:
            probes_model_name = 'ldapprobeanonbindlog'
            ldapprobelog_filter = {
                'ldapprobelog__created__gte': since_moment,
                'ldapprobelog__elapsed_bind__isnull': True,
            }

            subscription = f'{subscription}, anonymous bind'

        else:
            probes_model_name = 'ldapprobefullbindlog'
            ldapprobelog_filter = {
                'ldapprobelog__created__gte': since_moment,
                'ldapprobelog__elapsed_bind__isnull': False,
            }

            subscription = f'{subscription}, full bind'

        if perf_filter:
            subscription = f'{subscription}, perf'

        queryset = queryset.\
            filter(**ldapprobelog_filter).\
            annotate(number_of_failed_probes=Count(
                'ldapprobelog__failed',
                filter=Q(ldapprobelog__failed=True))).\
            annotate(number_of_successfull_probes=Count(
                'ldapprobelog__failed',
                filter=Q(ldapprobelog__failed=False))).\
            annotate(average_initialize_duration=Avg(
                'ldapprobelog__elapsed_initialize',
                filter=Q(ldapprobelog__failed=False)))

        if anon:
            queryset = queryset.\
                annotate(minimum_bind_duration=Min(
                    'ldapprobelog__elapsed_anon_bind',
                    filter=Q(ldapprobelog__failed=False))).\
                annotate(average_bind_duration=Avg(
                    'ldapprobelog__elapsed_anon_bind',
                    filter=Q(ldapprobelog__failed=False))).\
                annotate(maximum_bind_duration=Max(
                    'ldapprobelog__elapsed_anon_bind',
                    filter=Q(ldapprobelog__failed=False))).\
                annotate(minimum_read_root_dse_duration=Min(
                    'ldapprobelog__elapsed_read_root',
                    filter=Q(ldapprobelog__failed=False))).\
                annotate(average_read_root_dse_duration=Avg(
                    'ldapprobelog__elapsed_read_root',
                    filter=Q(ldapprobelog__failed=False))).\
                annotate(maximum_read_root_dse_duration=Max(
                    'ldapprobelog__elapsed_read_root',
                    filter=Q(ldapprobelog__failed=False))).values()
        else:
            queryset = queryset.\
                annotate(minimum_bind_duration=Min(
                    'ldapprobelog__elapsed_bind',
                    filter=Q(ldapprobelog__failed=False))).\
                annotate(average_bind_duration=Avg(
                    'ldapprobelog__elapsed_bind',
                    filter=Q(ldapprobelog__failed=False))).\
                annotate(maximum_bind_duration=Max(
                    'ldapprobelog__elapsed_bind',
                    filter=Q(ldapprobelog__failed=False))).\
                annotate(minimum_extended_search_duration=Min(
                    'ldapprobelog__elapsed_search_ext',
                    filter=Q(ldapprobelog__failed=False))).\
                annotate(average_extended_search_duration=Avg(
                    'ldapprobelog__elapsed_search_ext',
                    filter=Q(ldapprobelog__failed=False))).\
                annotate(maximum_extended_search_duration=Max(
                    'ldapprobelog__elapsed_search_ext',
                    filter=Q(ldapprobelog__failed=False))).values()

        queryset = cls.annotate_probe_details(
            probes_model_name, cls.annotate_orion_url(queryset))

    # TODO rework this to return the truly pertinent information, and move to
    #      subclass if possible.
        if 'node_dns' in [field.name for field in cls._meta.fields]:
            subscription = f'{subscription}, non orion'
            return (now, time_delta, subscription,
                    queryset.order_by('performance_bucket__name', 'node_dns'),
                    perf_filter)

        subscription = f'{subscription}, orion'
        return (now, time_delta, subscription,
                queryset.order_by('performance_bucket__name',
                                  'node__node_caption'),
                perf_filter)

    class Meta:
        abstract = True


class OrionADNode(BaseADNode, models.Model):
    """
    :class:`django.db.models.Model` class used for storing DNS information
    about `Windows` domain controller hosts defined on the `Orion`
    server

    `Domain Controller from Orion fields
    <../../../admin/doc/models/ldap_probe.orionnode>`__
    """
    node = models.OneToOneField(
        'orion_integration.OrionDomainControllerNode', db_index=True,
        blank=False, null=False, on_delete=models.CASCADE,
        verbose_name=_('Orion Node for Domain Controller'))

    def __str__(self):
        return self.node.node_dns or self.node.node_caption

    def get_node(self):
        return self.node.node_dns or self.node.ip_address

    @classmethod
    def _annotate_orion_url(cls, queryset=None):
        return queryset.annotate(
            orion_anchor=cls.sql_orion_anchor_field).annotate(
                orion_url=Concat(
                    Value(get_preference('orionserverconn__orion_server_url')),
                    F('node__details_url'),
                    output_field=URLField()
                )
            )

    @classmethod
    def _details_url_filter(cls):
        return '/?ad_orion_node__id='

    @property
    @mark_safe
    def orion_admin_url(self):
        """
        instance property containing the `URL` to the `Django admin` change
        form for this `AD` controller
        """
        return '<a href="%s">%s</>' % (reverse(
            'admin:orion_integration_orionnode_change', args=(self.node.id,)
        ), self.node.node_caption)

    @property
    @mark_safe
    def orion_url(self):
        """
        instance property containing the `URL` for the `Orion` node
        associated with this `AD` controller
        """
        return '<a href="%s%s">%s</a>' % (
            get_preference('orionserverconn__orion_server_url'),
            self.node.details_url, self.get_node())

    @classmethod
    def report_bad_fqdn(cls):
        """
        prepare data for reports about AD nodes defined in Orion but with
        the FQDN property missing
        """
        return cls.annotate_orion_url(
            cls.objects.filter(Q(node__node_dns__isnull=True) |
                               Q(node__node_dns='')).values())

    @classmethod
    def report_duplicate_nodes(cls):
        """
        prepare data for report about duplicate AD node entries on the Orion
        server

        In this case duplication is defined as `two or more Orion nodes that
        resolve to the same IP address`.

        """
        dupes = cls.objects.values('node__ip_address').\
            annotate(count_nodes=Count('node')).order_by().\
            filter(count_nodes__gt=1).\
            values_list('node__ip_address', flat=True)

        return cls.annotate_orion_url(
            cls.objects.filter(node__ip_address__in=dupes).values())

    class Meta:
        app_label = 'ldap_probe'
        verbose_name = _('Domain Controller from Orion')
        verbose_name_plural = _('Domain Controllers from Orion')
        ordering = ('node__node_caption', )


class NonOrionADNode(BaseADNode, models.Model):
    """
    :class:`django.db.models.Model` class used for storing DNS information
    about `Windows` domain controller hosts not available on the `Orion`
    server

    `Domain Controller not present in Orion fields
    <../../../admin/doc/models/ldap_probe.nonorionnode>`__
    """
    node_dns = models.CharField(
        _('Fully Qualified Domain Name (FQDN)'), max_length=255,
        db_index=True, unique=True, blank=False, null=False,
        help_text=_(
            'The FQDN of the domain controller host. It must respect the'
            ' rules specified in'
            ' `RFC1123 <http://www.faqs.org/rfcs/rfc1123.html>`__,'
            ' section 2.1')
    )

    def __str__(self):
        return self.get_node()

    def get_node(self):
        return self.node_dns

    @classmethod
    def _annotate_orion_url(cls, queryset):
        return queryset.annotate(
            orion_url=Concat(
                Value('AD node '), F('node_dns'),
                Value(' is not defined in Orion'), output_field=TextField())
        )

    @classmethod
    def _details_url_filter(cls):
        return '/?ad_node__id='

    def remove_if_in_orion(self):
        """
        if the domain controller host represented by this instance is also
        present on the `Orion` server, delete this instance

        We prefer to extract network node data from `Orion` instead of
        depending on some poor soul maintaining this model manually.

        There are some `AD` nodes in Orion that will match entries in this
        model but only if we consider the IP address. Since `AD` controllers
        always use fixed IP addresses (they better be), we will use IP
        addresses to eliminate the dupes.
        """
        try:
            ip_addresses = [
                addr[4][0] for addr in socket.getaddrinfo(self.node_dns, 0)
            ]
        except socket.gaierror:
            LOG.exception('Cannot resolve %s, deleting...', self)
            self.delete()
            return

        if OrionADNode.objects.filter(
                node__ip_address__in=ip_addresses).exists():

            LOG.info(
                'Found %s within the Orion AD nodes, deleting...', self)
            self.delete()

        return

    class Meta:
        app_label = 'ldap_probe'
        verbose_name = _('Domain Controller not present in Orion')
        verbose_name_plural = _('Domain Controllers not present in Orion')
        ordering = ['node_dns', ]
        get_latest_by = 'updated_on'


class LdapCredError(BaseModel, models.Model):
    """
    :class:`django.db.models.Model` class used for storing LDAP errors
    related to invalid credentials

    See `Common Active Directory Bind Errors
    <https://ldapwiki.com/wiki/Common%20Active%20Directory%20Bind%20Errors>`__.

    `LDAP Probe Log fields
    <../../../admin/doc/models/ldap_probe.ldapcrederror>`__
    """
    error_unique_identifier = models.CharField(
        _('LDAP Error Subcode'), max_length=3, db_index=True, unique=True,
        blank=False, null=False)
    short_description = models.CharField(
        _('Short Description'), max_length=128, db_index=True, blank=False,
        null=False)
    comments = models.TextField(_('Comments'), blank=True, null=True)

    def __str__(self):
        return (
            f'data {self.error_unique_identifier}: {self.short_description}')

    class Meta:
        app_label = 'ldap_probe'
        verbose_name = _('Active Directory Bind Error')
        verbose_name_plural = _('Common Active Directory Bind Errors')
        ordering = ['error_unique_identifier', ]
