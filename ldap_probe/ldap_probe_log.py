"""
ldap_probe.ldap_probe_log
-------------------------

This module contains the code related to logging ldap probes.

:copyright:

    Copyright 2020 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
import logging
import socket

from django.conf import settings
from django.db import models
from django.db.models import (
    Case, When, F, Value, TextField, Q)
from django.db.models.functions import Concat
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _

from citrus_borg.dynamic_preferences_registry import get_preference
from ldap_probe.managers import LdapProbeLogAnonBindManager, \
    LdapProbeLogFailedManager, LdapProbeLogFullBindManager
from ldap_probe.models import NonOrionADNode, OrionADNode
from p_soc_auto_base.utils import (
    MomentOfTime, get_uuid, get_absolute_admin_change_url)


LOG = logging.getLogger(__name__)


class LdapProbeLog(models.Model):
    """
    :class:`django.db.models.Model` class used for storing LDAP probing
    information

    `LDAP Probe Log fields
    <../../../admin/doc/models/ldap_probe.ldapprobelog>`__
    """
    csv_fields = [
        'uuid', 'ad_orion_node__node__node_caption', 'ad_node__node_dns',
        'elapsed_bind', 'elapsed_search_ext', 'elapsed_anon_bind']

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
    def error_report(cls, time_delta):
        """
        generate a :class:`django.db.models.query.QuerySet` object with
        the LDAP errors generated over the last $x minutes

        :arg time_delta: a :class:`datetime.duration` object that determines how
            far in the past to get failed LDAP probes from

        :returns: a :class:`django.db.models.query.QuerySet` with the
              failed LDAP probes over the defined period
        """
        when_ad_orion_node = When(
            ad_orion_node__isnull=False,
            then=Case(
                When(~Q(ad_orion_node__node__node_dns=''),
                     then=F('ad_orion_node__node__node_dns')),
                default=F('ad_orion_node__node__ip_address'),
                output_field=TextField()
            )
        )

        case_ad_node = Case(
            when_ad_orion_node, default=F('ad_node__node_dns'),
            output_field=TextField())

        # this will result in a query like
        # SELECT CASE WHEN `ldap_probe_ldapprobelog`.`ad_orion_node_id`
        # IS NOT NULL THEN CASE WHEN `orion_integration_orionnode`.`node_dns`
        # IS NOT NULL THEN `orion_integration_orionnode`.`node_dns`
        # ELSE `orion_integration_orionnode`.`ip_address`
        # END
        # ELSE `ldap_probe_nonorionadnode`.`node_dns`
        # END
        # AS `domain_controller_fqdn

        # We need this structure because this method forces all the
        # calculations to happen in the database engine.

        # The `SQL` fragment above is more or less the equivalent of
        # applying :meth:`BaseADNode.get_node` to each row in
        # :class:`LdapProbeLog`.

        since = MomentOfTime.past(time_delta=time_delta)

        return cls.objects.filter(failed=True, created_on__gte=since).\
            annotate(probe_url=Concat(
                Value(settings.SERVER_PROTO), Value('://'),
                Value(socket.getfqdn()), Value(':'),
                Value(settings.SERVER_PORT),
                Value('/admin/ldap_probe/ldapprobelogfailed/'), F('id'),
                Value('/change/'), output_field=TextField())).\
            annotate(domain_controller_fqdn=case_ad_node).\
            order_by('ad_node', '-created_on')

    def __str__(self):
        return f'LDAP probe {self.uuid} to {self.node}'

    @property
    def _node(self):
        return self.ad_orion_node or self.ad_node

    @property
    def node(self):
        """
        return the node that was the target of this `LDAP` probe
        """
        return self._node.get_node()

    @property
    def node_is_enabled(self):
        """
        is the node probed by this instance enabled?
        """
        return self._node.enabled

    @property
    def node_perf_bucket(self):
        """
        :returns: the performance bucket for this node
        :rtype: :class:`ADNodePerfBucket`
        """
        return self._node.performance_bucket

    @property
    def perf_alert(self):
        """
        flag for considering if an instance of this class must trigger a
        performance alert

        :returns: `True` if there is a timing from the probe above the err
                  threshold, and ldap_perf_raise_all is `True`.
        :rtype: bool
        """
        return get_preference('ldapprobe__ldap_perf_raise_all')\
            and self._perf_level(self.node_perf_bucket.avg_err_threshold)

    @property
    def perf_warn(self):
        """
        flag for considering if an instance of this class must trigger a
        performance warning

        :returns: `True` if there is a timing from the probe above the warn
                  threshold, and ldap_perf_raise_all is `True`.
        :rtype: bool
        """
        return get_preference('ldapprobe__ldap_perf_raise_all')\
            and self._perf_level(self.node_perf_bucket.avg_warn_threshold)

    @property
    def perf_err(self):
        """
        flag for considering if an instance of this class must trigger a
        performance never exceed alert

        :returns: `True` if there is a timing from the probe above the alert
                  threshold.
        :rtype: bool
        """
        return self._perf_level(self.node_perf_bucket.alert_threshold)

    def _perf_level(self, level):
        return any(
            elapsed is not None and elapsed >= level
            for elapsed in
            [self.elapsed_bind, self.elapsed_anon_bind, self.elapsed_search_ext,
             self.elapsed_read_root]
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

        :arg dict probe_data: the data returned by the LDAP probe
        """
        # Pop the ad_controller, because it is not a field of this model
        ad_controller = probe_data.pop('ad_controller')
        ldap_probe_log_entry = cls(**probe_data)

        # Set the appropriate field (orion or non) to the ad_controller
        if isinstance(ad_controller, OrionADNode):
            ldap_probe_log_entry.ad_orion_node = ad_controller
        else:
            ldap_probe_log_entry.ad_node = ad_controller

        ldap_probe_log_entry.save()

        LOG.debug('created %s', ldap_probe_log_entry)

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
    objects = LdapProbeLogFailedManager()

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
    objects = LdapProbeLogFullBindManager()

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
