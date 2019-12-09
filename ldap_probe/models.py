"""
ldap_probe.models
-----------------

This module contains the :class:`django.db.models.Model` models for the
:ref:`Domain Controllers Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Dec. 6, 2019

"""
import decimal
import logging
import socket

from django.conf import settings
from django.db import models
from django.db.models import (
    Case, When, F, Value, TextField, URLField, Count, Avg, Min, Max, Q)
from django.db.models.functions import Concat
from django.core import validators
from django.urls import reverse
from django.utils import timezone
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from citrus_borg.dynamic_preferences_registry import get_preference
from p_soc_auto_base.models import BaseModel, BaseModelWithDefaultInstance
from p_soc_auto_base.utils import (
    get_uuid, get_absolute_admin_change_url, MomentOfTime,
)


LOGGER = logging.getLogger('ldap_probe_log')


def _get_default_ldap_search_base():
    """
    get the default value for the :attr:`LDAPBindCred.ldap_search_base`
    attribute
    """
    return get_preference('ldapprobe__search_dn_default')

# pylint: disable=too-few-public-methods


class LdapProbeLogFullBindManager(models.Manager):
    """
    custom :class:`django.db.models.Manager` used by the
    :class:`LdapProbeLogFullBind` model

    We have observed that the default set of `Windows` domain credentials
    will allow full LDAP binds for a limited number of `AD` controllers.
    By design LDAP probe data collected from these `AD` controllers will
    present with :attr:`LdapProbeLog.elapsed_bind` values that are not
    null (`None` in `Python` speak).
    """

    def get_queryset(self):  # pylint: disable=no-self-use
        """
        override :meth:`django.db.models.Manager.get_queryset`

        See `Modifying a manager's initial QuerySet
        <https://docs.djangoproject.com/en/2.2/topics/db/managers/#modifying-a-manager-s-initial-queryset>`__
        in the `Django` docs.

        :returns: a :class:`django.db.models.query.QuerySet` with the
            :class:`LdapProbeLog` instances that contain timing data for
            `LDAP` full bind operations

        """
        return LdapProbeLog.objects.filter(elapsed_bind__isnull=False)


class LdapProbeLogAnonBindManager(models.Manager):
    """
    custom :class:`django.db.models.Manager` used by the
    :class:`LdapProbeLogFullBind` model

    We have observed that the default set of `Windows` domain credentials
    will not allow full LDAP binds (see :class:`LdapProbeLogFullBindManager`)
    for most of `AD` controllers.
    By design LDAP probe data collected from these `AD` controllers will
    present with :attr:`LdapProbeLog.elapsed_anon_bind` values that are not
    null (`None` in `Python` speak).

    """

    def get_queryset(self):  # pylint: disable=no-self-use
        """
        override :meth:`django.db.models.Manager.get_queryset`

        See `Modifying a manager's initial QuerySet
        <https://docs.djangoproject.com/en/2.2/topics/db/managers/#modifying-a-manager-s-initial-queryset>`__
        in the `Django` docs.

        :returns: a :class:`django.db.models.query.QuerySet` with the
            :class:`LdapProbeLog` instances that contain timing data for
            `LDAP` anonymous bind operations

        """
        return LdapProbeLog.objects.filter(elapsed_anon_bind__isnull=False)


class LdapProbeLogFailedManager(models.Manager):
    """
    custom :class:`django.db.models.Manager` used by the
    :class:`LdapProbeLogFailed` model

    """

    def get_queryset(self):  # pylint: disable=no-self-use
        """
        override :meth:`django.db.models.Manager.get_queryset`

        See `Modifying a manager's initial QuerySet
        <https://docs.djangoproject.com/en/2.2/topics/db/managers/#modifying-a-manager-s-initial-queryset>`__
        in the `Django` docs.

        :returns: a :class:`django.db.models.query.QuerySet` with the
            :class:`LdapProbeLog` failed instances

        """
        return LdapProbeLog.objects.filter(failed=True)

# pylint: enable=too-few-public-methods


class LDAPBindCred(BaseModelWithDefaultInstance, models.Model):
    """
    :class:`django.db.models.Model` class used for storing credentials used
    for probing `Windows` domain controllers

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


class BaseADNode(BaseModel, models.Model):
    """
    `Django abastract model
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#abstract-base-classes>`__
    for storing information about `Windows` domain controller hosts
    """
    ldap_bind_cred = models.ForeignKey(
        'ldap_probe.LDAPBindCred', db_index=True, blank=False, null=False,
        default=LDAPBindCred.get_default, on_delete=models.PROTECT,
        verbose_name=_('LDAP Bind Credentials'))

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
    to append a meaningfull field to a queryset. If
    :attr:`orion_integration.models.OrionNode.node_dns` exists, it will
    be placed in a :class:`django.db.models.query.QuerySet`. Otherwise,
    the :attr:`orion_integration.models.OrionNode.ip_address` will be
    used.

    """

    def get_node(self):  # pylint: disable=inconsistent-return-statements
        """
        get node network information in either `FQDN` or `IP` address format

        We need this function mostly for retrieving node address information
        from `Orion` nodes. `Orion` nodes are guaranteed to have an `IP`
        address but sometimes they don't have a valid `FQDN`.
        """
        if hasattr(self, 'node_dns'):
            return getattr(self, 'node_dns')

        if hasattr(self, 'node'):
            node = getattr(self, 'node')
            if node.node_dns:
                return node.node_dns
            return node.ip_address

    @classmethod
    def annotate_orion_url(cls, queryset=None):
        """
        annotate
        <https://docs.djangoproject.com/en/2.2/topics/db/aggregation/>`__
        a :class:`queryset <django.db.models.query.QuerySet>` with the
        absolute `URL` of the node definition on the `Orion` server if
        possible or with a 'this node is not in orion' message

        The name of this annotation will be 'orion_url'.

        :arg queryset: a :class:`django.db.models.query.QuerySet` based
            on one of the models inheriting from :class:`BaseADNode`

            If `None`, one will be created by this method

        :returns: the :class:`django.db.models.query.QuerySet` with the
            'orion_url' field included

            Note that the :class:`django.db.models.query.QuerySet`is filtered
            to return only `enabled` nodes
        """
        if queryset is None:
            queryset = cls.objects.filter(enabled=True)

        if 'node_dns' in [field.name for field in cls._meta.fields]:
            queryset = queryset.annotate(
                orion_url=Concat(
                    Value('AD node '), F('node_dns'),
                    Value(' is not defined in Orion'),
                    output_field=TextField()
                )
            )
        else:
            queryset = queryset.\
                annotate(orion_anchor=cls.sql_orion_anchor_field).\
                annotate(
                    orion_url=Concat(
                        Value(get_preference(
                            'orionserverconn__orion_server_url')),
                        F('node__details_url'),
                        output_field=URLField()
                    )
                )

        return queryset.values()

    @classmethod
    def annotate_probe_details(cls, probes_model_name, queryset=None):
        """
        annotate a :class:`queryset <django.db.models.query.QuerySet>`
        based on classes inheriting from :class:`BaseADNode` model with
        the absolute `URL` for the details of the `LDAP` probes executed
        against the AD node

        Note that this method will be very expensive when invoked
        against a queryset that does not restrict the number of
        :class:`LdapProbeLog` rows.

        The annotation should look something like
        'http://lvmsocq01.healthbc.org:8091/admin/ldap_probe/' + \
        'ldapprobefullbindlog/?ad_node__isnull=True' + \
        '&ad_orion_node__id__exact=3388'.
        """
        if queryset is None:
            queryset = cls.annotate_orion_url()

        if 'node_dns' in [field.name for field in cls._meta.fields]:
            url_filters = '/?ad_orion_node__isnull=True&ad_node__id__exact='
        else:
            url_filters = '/?ad_node__isnull=True&ad_orion_node__id__exact='

        return queryset.annotate(probes_url=Concat(
            Value(settings.SERVER_PROTO), Value('://'),
            Value(socket.getfqdn()), Value(':'),
            Value(settings.SERVER_PORT),
            Value('/admin/ldap_probe/'), Value(probes_model_name),
            Value(url_filters), F('id'), output_field=TextField())).values()

    @classmethod
    def report_probe_aggregates(
            cls,
            queryset=None, anon=False, perf_filter=None, **time_delta_args):
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

        :arg str perf_filter: apply filters for performance degradation if
            this argument is provided

            If this argument is `None`, this method will not filter for
            performance degradation results.

            Otherwise, the argument will be updated to a
            :class:`deciaml.Decimal` value based on the original value:

            * if the value is 'warning', update the argument to the value
              provided by the user preference defined in
              :class:`citrus_borg.dynamic_preferences_registry.LdapPerfWarnTreshold`

            * else if the value is 'alert', update the argument to the value
              provided by the user preference defined in
              :class:`citrus_borg.dynamic_preferences_registry.LdapPerfAlertTreshold`

            * else, try to convert the original value to
              :class:`deciaml.Decimal` and raise a
              :exc:`exceptions.ValueError` if the conversion fails

        :arg time_delta_args: optional named arguments that are used to
            initialize a :class:`datetime.duration` object

            If not present, the method will use the period defined by the
            :class:`citrus_borg.dynamic_preferences_registry.LdapReportPeriod`
            user preference

        :returns:

            * the moments used to filter the data in the report by time

            * the :attr:`subscription
              <ssl_cert_tracker.models.Subscription.subscription>` that will
              be used to deliver this report via email

            * the :class:`django.db.models.query.QuerySet` based on one
              of the classes inheriting from  the :class:`BaseADNode` abstract
              model

              Depending on the calling class the following aggregates with
              regards to LDAP probes are placed in the queryset

                  * the number of failed probes

                  * the number of successful probes

                  * average timing for initialize calls of the successful
                    probes

                  * min, max, average timing for `bind` calls or `anonymous
                   bind` calls of the successful probes

                  * min, max, average timing for `extended search` calls or
                    `read root dse` calls of the successful probes

        :raises:

            :exc:`exceptions.ValueError` if the `perf_filter` argument
            is not `None` and it cannot be used to initialize a
            :class:`decimal.Decimal` object

        .. todo::

            Add a catch for no nodes available.

            This is a bad thing if there
            are no orion nodes (treat this case as a fully separate alert).

            However, the normal case is that all `AD` nodes are now
            defined in Orion and in that case, we can safely abort
            report calls for non Orion nodes.


        """
        def resolve_perf_filter(perf_filter):
            """
            embedded function for resolving the value of the `perf_filter`
            argument
            """
            if perf_filter is None:
                return None

            if perf_filter.lower() in ['warning']:
                perf_filter = get_preference('ldapprobe__ldap_perf_warn')
            elif perf_filter.lower() in ['alert']:
                perf_filter = get_preference('ldapprobe__ldap_perf_alert')
            else:
                try:
                    perf_filter = decimal.Decimal(perf_filter)
                except decimal.InvalidOperation:
                    raise ValueError(
                        f'{type(perf_filter)} object {perf_filter}'
                        ' cannot be converted to decimal')

            return perf_filter

        perf_filter = resolve_perf_filter(perf_filter)

        subscription = 'LDAP: summary report'
        if queryset is None:
            queryset = cls.objects.filter(enabled=True)

        if time_delta_args:
            time_delta = timezone.timedelta(**time_delta_args)
        else:
            time_delta = get_preference('ldapprobe__ldap_reports_period')

        since_moment = MomentOfTime.past(time_delta=time_delta)
        now = timezone.now()

        if anon:
            probes_model_name = 'ldapprobeanonbindlog'
            ldapprobelog_filter = {
                'ldapprobelog__created_on__gte': since_moment,
                'ldapprobelog__elapsed_bind__isnull': True,
            }

            subscription = f'{subscription}, anonymous bind'

            if perf_filter:
                ldapprobelog_filter[
                    'ldapprobelog__elapsed_anon_bind__gte'] = perf_filter
                subscription = f'{subscription}, perf'

        else:
            probes_model_name = 'ldapprobefullbindlog'
            ldapprobelog_filter = {
                'ldapprobelog__created_on__gte': since_moment,
                'ldapprobelog__elapsed_bind__isnull': False,
            }

            subscription = f'{subscription}, full bind'

            if perf_filter:
                ldapprobelog_filter[
                    'ldapprobelog__elapsed_bind__gte'] = perf_filter
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

        if 'node_dns' in [field.name for field in cls._meta.fields]:
            subscription = f'{subscription}, non orion'
            return (now, time_delta, subscription,
                    queryset.order_by('node_dns'), perf_filter)

        subscription = f'{subscription}, orion'
        return (now, time_delta, subscription,
                queryset.order_by('node__node_caption'), perf_filter)

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
        if self.node.node_dns:
            return self.node.node_dns

        return self.node.node_caption

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
        return cls.objects.filter(
            Q(node__node_dns__isnull=True) | Q(node__node_dns__iexact=''))

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

    @classmethod
    def report_nodes(cls):
        """
        prepare report data for `AD` nodes that are not defined on the
        `Orion` server

        :returns: the :class:`django.db.models.query.QuerySet` based on
              the :class:`NonOrionADNode` model

        """
        return cls.objects.filter(enabled=True).order_by('node_dns')

    def __str__(self):
        return self.node_dns

    def remove_if_in_orion(self, logger=LOGGER):
        """
        if the domain controller host represented by this instance is also
        present on the `Orion` server, delete this istance

        We prefer to extract network node data from `Orion` instead of
        depending on some poor soul maintaining this model manually.

        There are some `AD` nodes in Orion that will match entries in this
        model but only if we consider the IP address. Since `AD` controllers
        always use fixed IP addresses (they better be), we will use IP
        addresses to eliminate the dupes.
        """
        ip_addresses = None

        try:
            ip_addresses = [
                addr[4][0] for addr in socket.getaddrinfo(self.node_dns, 0)
            ]
        except:  # pylint: disable=bare-except
            logger.error('Cannot resolve %s, deleting...', self)
            self.delete()
            return

        if OrionADNode.objects.filter(
                node__ip_address__in=ip_addresses).exists():

            logger.info(
                'Found %s within the Orion AD nodes, deleting...', self)
            self.delete()

        return

    class Meta:
        app_label = 'ldap_probe'
        verbose_name = _('Domain Controller not present in Orion')
        verbose_name_plural = _('Domain Controllers not present in Orion')
        ordering = ['node_dns', ]
        get_latest_by = 'updated_on'


class LdapProbeLog(models.Model):
    """
    :class:`django.db.models.Model` class used for storing LDAP probing
    information

    `LDAP Probe Log fields
    <../../../admin/doc/models/ldap_probe.ldapprobelog>`__
    """
    uuid = models.UUIDField(
        _('UUID'), unique=True, db_index=True, blank=False, null=False,
        default=get_uuid)
    ad_orion_node = models.ForeignKey(
        OrionADNode, db_index=True, blank=True, null=True,
        on_delete=models.CASCADE, verbose_name=_('AD controller (Orion)'))
    ad_node = models.ForeignKey(
        NonOrionADNode, db_index=True, blank=True, null=True,
        on_delete=models.CASCADE, verbose_name=_('AD controller'))
    elapsed_initialize = models.DecimalField(
        _('LDAP initialization duration'), max_digits=9, decimal_places=6,
        blank=True, null=True)
    elapsed_bind = models.DecimalField(
        _('LDAP bind duration'), max_digits=9, decimal_places=6,
        blank=True, null=True)
    elapsed_anon_bind = models.DecimalField(
        _('LDAP anonymous bind duration'), max_digits=9, decimal_places=6,
        blank=True, null=True)
    elapsed_read_root = models.DecimalField(
        _('LDAP read root DSE duration'), max_digits=9, decimal_places=6,
        blank=True, null=True)
    elapsed_search_ext = models.DecimalField(
        _('LDAP extended search duration'), max_digits=9, decimal_places=6,
        blank=True, null=True)
    ad_response = models.TextField(
        _('AD controller response'), blank=True, null=True)
    errors = models.TextField(
        _('Errors'), blank=True, null=True)
    created_on = models.DateTimeField(
        _('created on'), db_index=True, auto_now_add=True,
        help_text=_('object creation time stamp'))
    is_expired = models.BooleanField(
        _('Probe data has expired'), db_index=True, blank=False, null=False,
        default=False)
    failed = models.BooleanField(
        _('Probe failed'), db_index=True, blank=False, null=False,
        default=False)

    @classmethod
    def error_report(cls, **time_delta_args):
        """
        generate a :class:`django.db.models.query.QuerySet` object with
        the LDAP errors generated over the last $x minutes

        :arg time_delta_args: optional named arguments that are used to
            initialize a :class:`datetime.duration` object

            If not present, the method will use the period defined by the
            :class:`citrus_borg.dynamic_preferences_registry.LdapReportPeriod`
            user preference

        :returns:

            * the moments used to filter the data in the report by time

            * :class:`django.db.models.query.QuerySet` with the
              failed LDAP probes over the defined period

        """
        when_ad_orion_node = When(
            ad_orion_node__isnull=False,
            then=Case(When(
                ~Q(ad_orion_node__node__node_dns__iexact=''),
                then=F('ad_orion_node__node__node_dns')),
                default=F('ad_orion_node__node__ip_address'),
                output_field=TextField()))
        """
        :class:`django.db.models.When` instance that will translate into
        an `SQL` `WHEN` clause
        """

        case_ad_node = Case(
            when_ad_orion_node, default=F('ad_node__node_dns'),
            output_field=TextField())
        """
        :class:`django.db.models.Case` instance that will translate into
        an `SQL` `WHEN` clause

        Together with the previous attribute, this will result into
        something like
        SELECT CASE WHEN `ldap_probe_ldapprobelog`.`ad_orion_node_id`
        IS NOT NULL THEN CASE WHEN `orion_integration_orionnode`.`node_dns`
        IS NOT NULL THEN `orion_integration_orionnode`.`node_dns`
        ELSE `orion_integration_orionnode`.`ip_address`
        END
        ELSE `ldap_probe_nonorionadnode`.`node_dns`
        END
        AS `domain_controller_fqdn

        We need this structure because this method forces all the
        calculations to happen in the database engine.

        The `SQL` fragment above is more or less the equivalent of
        applying :meth:`BaseADNode.get_node` to each row in
        :class:`LdapProbeLog`.
        """

        if time_delta_args:
            time_delta = timezone.timedelta(**time_delta_args)
        else:
            time_delta = get_preference('ldapprobe__ldap_reports_period')

        since = MomentOfTime.past(time_delta=time_delta)
        now = timezone.now()

        queryset = cls.objects.filter(failed=True, created_on__gte=since).\
            annotate(probe_url=Concat(
                Value(settings.SERVER_PROTO), Value('://'),
                Value(socket.getfqdn()), Value(':'),
                Value(settings.SERVER_PORT),
                Value('/admin/ldap_probe/ldapprobelogfailed/'), F('id'),
                Value('/change/'), output_field=TextField())).\
            annotate(domain_controller_fqdn=case_ad_node).\
            order_by('ad_node', '-created_on')

        print(queryset.query)

        return now, time_delta, queryset

    def __str__(self):
        return f'LDAP probe {self.uuid} to {self.node}'

    @property
    def node(self):
        """
        return the node that was the target of this `LDAP` probe
        """
        if self.ad_orion_node:
            return self.ad_orion_node.get_node()

        return self.ad_node.get_node()

    @property
    def perf_alert(self):
        """
        flag for considering if an instance of this class must trigger a
        performance alert

        In plain English, this method translates into::

            Give me all the elapsed_foo fields that are not `None`. Then,
            out of these not `None` fields, if any of them is greater than
            a threshold, return `True`. Otherwise, return `False`.

        :returns: `True/False`
        :rtype: bool
        """
        return any(
            [
                elapsed for elapsed in
                [
                    self_elapsed for self_elapsed in
                    [
                        self.elapsed_bind, self.elapsed_anon_bind,
                        self.elapsed_search_ext, self.elapsed_read_root
                    ]
                    if self_elapsed is not None
                ]
                if elapsed >= get_preference('ldapprobe__ldap_perf_alert')
            ]
        )

    @property
    def perf_warn(self):
        """
        flag for considering if an instance of this class must trigger a
        performance warning

        :returns: `True/False`
        :rtype: bool
        """
        return any(
            [
                elapsed for elapsed in
                [
                    self_elapsed for self_elapsed in
                    [
                        self.elapsed_bind, self.elapsed_anon_bind,
                        self.elapsed_search_ext, self.elapsed_read_root
                    ]
                    if self_elapsed is not None
                ]
                if elapsed >= get_preference('ldapprobe__ldap_perf_warn')
            ]
        )

    @property
    @mark_safe
    def absolute_url(self):
        """
        absolute `URL` for the `Django admin` form for this instance

        Note that there is no :class:`Django admin class
        <django.contrib.admin.ModelAdmin>` matching this model. We will
        have to use `admin views` pointing to the modles proxied from this
        model.

        :returns: the absolute `URL` for the admin pages showing this
            instance

        """
        admin_view = 'admin:ldap_probe_ldapprobeanonbindlog_change'

        if self.failed:
            admin_view = 'admin:ldap_probe_ldapprobelogfailed_change'

        if self.elapsed_bind:
            admin_view = 'admin:ldap_probe_ldapprobefullbindlog_change'

        return get_absolute_admin_change_url(
            admin_view=admin_view, obj_pk=self.id, obj_anchor_name=str(self))

    @property
    @mark_safe
    def ad_node_orion_url(self):
        """
        the `URL` for the `Orion` definition of the `AD` controller
        that was the destination of this probe
        """
        if self.ad_orion_node:
            return self.ad_orion_node.orion_url
        return None

    @classmethod
    def create_from_probe(cls, probe_data):
        """
        `class method
        <https://docs.python.org/3.6/library/functions.html#classmethod>`__
        that creates an instance of the :class:`LdapProbeLog`

        :arg probe_data: the data returned by the LDAP probe
        :type probe_data: :class:`ldap_probe.ad_probe.ADProbe`

        :arg logger: :class:`logging.Logger instance

        :returns: the new :class:`LdapProbeLog` instance
        """
        ldap_probe_log_entry = cls(
            elapsed_initialize=probe_data.elapsed.elapsed_initialize,
            elapsed_bind=probe_data.elapsed.elapsed_bind,
            elapsed_anon_bind=probe_data.elapsed.elapsed_anon_bind,
            elapsed_read_root=probe_data.elapsed.elapsed_read_root,
            elapsed_search_ext=probe_data.elapsed.elapsed_search_ext,
            ad_response=probe_data.ad_response, errors=probe_data.errors,
            failed=probe_data.failed
        )

        if isinstance(probe_data.ad_controller, OrionADNode):
            ldap_probe_log_entry.ad_orion_node = probe_data.ad_controller
        else:
            ldap_probe_log_entry.ad_node = probe_data.ad_controller

        try:
            ldap_probe_log_entry.save()
        except Exception as err:
            raise err

        return f'created {ldap_probe_log_entry}'

    class Meta:
        app_label = 'ldap_probe'
        verbose_name = _('AD service probe')
        verbose_name_plural = _('AD service probes')
        ordering = ('-created_on', )


class LdapProbeLogFailed(LdapProbeLog):
    """
    `Proxy model
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models>`__
    that shows only :class:`LdapProbeLog` instances with full `AD` probe
    data
    """
    obejcts = LdapProbeLogFailedManager()

    class Meta:
        proxy = True
        verbose_name = _('Failed AD service probe')
        verbose_name_plural = _('Failed AD service probes')


class LdapProbeFullBindLog(LdapProbeLog):
    """
    `Proxy model
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models>`__
    that shows only :class:`LdapProbeLog` instances with full `AD` probe
    data
    """
    obejcts = LdapProbeLogFullBindManager()

    class Meta:
        proxy = True
        verbose_name = _('AD service probe with full data')
        verbose_name_plural = _('AD service probes with full data')


class LdapProbeAnonBindLog(LdapProbeLog):
    """
    `Proxy model
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models>`__
    that shows only :class:`LdapProbeLog` instances with limited `AD` probe
    data
    """
    objects = LdapProbeLogAnonBindManager()

    class Meta:
        proxy = True
        verbose_name = _('AD service probe with limited data')
        verbose_name_plural = _('AD service probes with limited data')


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
