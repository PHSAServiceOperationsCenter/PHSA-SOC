"""
ldap_probe.admin
-----------------

This module contains the `Django admin
<https://docs.djangoproject.com/en/2.2/ref/contrib/admin/#module-django.contrib.admin>`__
classes for the :ref:`Active Directory Services Monitoring Application`.

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from django.contrib import admin
from django.forms.widgets import PasswordInput
from django.utils.translation import gettext_lazy as _
from rangefilter.filter import DateTimeRangeFilter

from ldap_probe import models
from p_soc_auto_base import admin as base_admin, utils


class LdapProbeBaseAdmin(base_admin.BaseAdmin, admin.ModelAdmin):
    """
    Base class for other :class:`Django admin classes
    <django.contrib.admin.ModelAdmin>` in this module
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        override
        :meth:`django.contrib.admin.ModelAdmin.formfield_for_foreignkey`

        provide specialized drop-down values for 'ldap_bind_cred`,
        `ad_orion_node`, and `ad_node` `ForeignKey` fields.
        """
        if db_field.name == 'ldap_bind_cred':
            kwargs['queryset'] = models.LDAPBindCred.active
            kwargs['initial'] = models.LDAPBindCred.get_default()

        elif db_field.name == 'ad_orion_node':
            kwargs['queryset'] = models.OrionADNode.active

        elif db_field.name == 'ad_node':
            kwargs['queryset'] = models.NonOrionADNode.active

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def show_avg_warn_threshold(self, obj):
        """
        show :attr:`ldap_probe.models.ADNodePerfBucket.avg_warn_threshold`
        in the `Django admin` interface
        """
        try:
            return utils.show_milliseconds(
                obj.performance_bucket.avg_warn_threshold)
        except AttributeError:
            return None
    show_avg_warn_threshold.short_description = _(
        'Response Time Warning')

    def show_avg_err_threshold(self, obj):
        """
        show :attr:`ldap_probe.models.ADNodePerfBucket.avg_err_threshold`
        in the `Django admin` interface
        """
        try:
            return utils.show_milliseconds(
                obj.performance_bucket.avg_err_threshold)
        except AttributeError:
            return None
    show_avg_err_threshold.short_description = _(
        'Response Time Error')

    def show_alert_threshold(self, obj):
        """
        show :attr:`ldap_probe.models.ADNodePerfBucket.alert_threshold`
        in the `Django admin` interface
        """
        try:
            return utils.show_milliseconds(
                obj.performance_bucket.alert_threshold)
        except AttributeError:
            return None
    show_alert_threshold.short_description = _(
        'Response Time Alert')


@admin.register(models.ADNodePerfBucket)
class AdNodePerfBucketAdmin(LdapProbeBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.ADNodePerfBucket`
    """
    list_display = ('name', 'enabled', 'is_default', 'avg_warn_threshold',
                    'avg_err_threshold', 'alert_threshold', 'updated_on',
                    'updated_by', )
    list_editable = ('enabled', 'is_default', 'avg_warn_threshold',
                     'avg_err_threshold', 'alert_threshold', )
    list_filter = ('enabled', )
    search_fields = ('name', 'notes', )


@admin.register(models.OrionADNode)
class OrionADNodeAdmin(LdapProbeBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.OrionADNode`
    """
    list_display_links = ('show_node_caption', )
    list_display = ('show_node_caption', 'enabled', 'ldap_bind_cred',
                    'node_dns', 'ip_address', 'performance_bucket',
                    'show_avg_warn_threshold', 'show_avg_err_threshold',
                    'show_alert_threshold', 'show_orion_admin_url',
                    'show_orion_url', 'site', )
    list_editable = ('enabled', 'ldap_bind_cred', 'performance_bucket')
    readonly_fields = ('show_node_caption', 'node_dns', 'ip_address',
                       'show_orion_admin_url', 'show_orion_url', 'site',
                       'show_avg_warn_threshold', )
    search_fields = ('node__node_caption', 'node__node_dns',
                     'node__ip_address', 'node__location', 'node__site')
    list_filter = ('node__site', 'node__location', )
    exclude = ('node', )

    def has_add_permission(self, request):
        """
        :class:`ldap_probe.models.OrionADNode` instances are created
        automatically in the background

        We override :meth:`django.contrib.admin.ModelAdmin.has_add_permission`
        to prevent anybody from using the admin forms to create such
        instances.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        :class:`ldap_probe.models.OrionADNode` instances are maintained
        automatically in the background

        We override :meth:`django.contrib.admin.ModelAdmin.has_add_permission`
        to prevent anybody from using the admin forms to delete such
        instances.
        """
        return False

    # pylint: disable=no-self-use

    def show_node_caption(self, obj):
        """
        show the node caption as known to the `Orion` server
        """
        if obj.node.node_caption:
            return obj.node.node_caption
        return None
    show_node_caption.short_description = _('AD Orion node')

    def node_dns(self, obj):
        """
        show the node `FQDN` as known to the `Orion` server
        """
        if obj.node.node_dns:
            return obj.node.node_dns
        return None
    node_dns.short_description = _('FQDN')

    def show_orion_admin_url(self, obj):
        """
        show the `URL` to the `Django admin change form` associated with
        this `AD` node
        """
        return obj.orion_admin_url
    show_orion_admin_url.short_description = _(
        'Local definition for this node')

    def show_orion_url(self, obj):
        """
        show the `URL` to the definition of this `AD` controller on the
        `Orion` server
        """
        return obj.orion_url
    show_orion_url.short_description = _(
        'Orion definition for this node')

    def ip_address(self, obj):
        """
        show the `IP` address as known to the `Orion` server
        """
        if obj.node.ip_address:
            return obj.node.ip_address
        return None
    ip_address.short_description = _('IP address')

    def site(self, obj):
        """
        show the site of this `AD` controller as defined in Orion
        """
        if obj.node.site:
            return obj.node.site
        return None
    site.short_description = _('Site')

    def location(self, obj):
        """
        show the location of this `AD` controller as defined in Orion
        """
        if obj.node.location:
            return obj.node.location
        return None
    location.short_description = _('Location')

    # pylint: enable=no-self-use


@admin.register(models.NonOrionADNode)
class NonOrionADNodeAdmin(LdapProbeBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.NonOrionADNode`
    """
    list_display = ('node_dns', 'enabled', 'ldap_bind_cred',
                    'performance_bucket', 'show_avg_warn_threshold',
                    'show_avg_err_threshold', 'show_alert_threshold',
                    'updated_on', 'updated_by', )
    list_editable = ('enabled', 'ldap_bind_cred', 'performance_bucket', )
    list_filter = ('enabled', 'ldap_bind_cred__domain',
                   'ldap_bind_cred__username', )
    search_fields = ('node_dns', )


@admin.register(models.LDAPBindCred)
class LDAPBindCredAdmin(LdapProbeBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.LDAPBindCred`
    """
    list_display_links = ('show_account',)
    list_display = ('show_account', 'enabled', 'domain',
                    'username', 'is_default', 'ldap_search_base',
                    'updated_on', 'updated_by')
    list_editable = ('enabled', 'domain', 'username', 'is_default',
                     'ldap_search_base',)
    list_filter = ('enabled', 'domain')
    search_fields = ('domain', 'username')
    readonly_fields = ('show_account', )

    def show_account(self, obj):  # pylint: disable=no-self-use
        """
        display combined field for windows domain accounts
        """
        return '%s\\%s' % (obj.domain, obj.username)
    show_account.short_description = _('Domain Account')

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'password':
            kwargs['widget'] = PasswordInput(render_value=True)

        return super().formfield_for_dbfield(db_field, request, **kwargs)


class LdapProbeLogAdminBase(admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` base class for admin classes
    used by `proxy models
    <https://docs.djangoproject.com/en/2.2/topics/db/models/#proxy-models>`__
    that inherit from :class:`ldap_probe.models.LdapProbeLog`
    """

    def has_add_permission(self, request):
        """
        :class:`ldap_probe.models.LdapProbeLog` instances are created
        automatically in the background

        We override :meth:`django.contrib.admin.ModelAdmin.has_add_permission`
        to prevent anybody from using the admin forms to create such
        instances.
        """
        return False

    def has_delete_permission(self, request, obj=None):
        """
        :class:`ldap_probe.models.LdapProbeLog` instances are maintained
        automatically in the background

        We override :meth:`django.contrib.admin.ModelAdmin.has_add_permission`
        to prevent anybody from using the admin forms to delete such
        instances.
        """
        return False

    def get_readonly_fields(self, request, obj=None):
        """
        all the fields on the `Django admin` forms must be read only
        """
        return [field.name for field in self.model._meta.fields]


@admin.register(models.LdapProbeLogFailed)
class LdapProbeLogFailedAdmin(LdapProbeLogAdminBase, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.LdapProbeFailed`
    """
    list_display = ('uuid', 'ad_orion_node', 'ad_node', 'errors', 'created_on')
    list_filter = (
        ('ad_node', admin.RelatedOnlyFieldListFilter),
        ('ad_orion_node', admin.RelatedOnlyFieldListFilter),
        ('created_on', DateTimeRangeFilter),
    )
    search_fields = ('ad_node', 'ad_orion_node__node__node_dns',
                     'ad_orion_node__node__node_caption',
                     'ad_orion_node__node__ip_address',)


@admin.register(models.LdapProbeFullBindLog)
class LdapProbeFullBindLogAdmin(LdapProbeLogAdminBase, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.LdapProbeFullBindLog`
    """
    list_display = ('uuid', 'ad_orion_node', 'ad_node', 'failed',
                    'elapsed_initialize', 'elapsed_bind', 'elapsed_search_ext',
                    'created_on', )
    list_filter = (('ad_node', admin.RelatedOnlyFieldListFilter),
                   ('ad_orion_node',
                    admin.RelatedOnlyFieldListFilter),
                   ('created_on', DateTimeRangeFilter), )
    search_fields = ('ad_node', 'ad_orion_node__node__node_dns',
                     'ad_orion_node__node__node_caption',
                     'ad_orion_node__node__ip_address', )


@admin.register(models.LdapProbeAnonBindLog)
class LdapProbeAnonBindLogAdmin(LdapProbeLogAdminBase, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.LdapProbeAnonBindLog`
    """
    list_display = ('uuid', 'ad_orion_node', 'ad_node', 'failed',
                    'elapsed_initialize', 'elapsed_anon_bind',
                    'elapsed_read_root', 'created_on', )
    list_filter = (('ad_node', admin.RelatedOnlyFieldListFilter),
                   ('ad_orion_node',
                    admin.RelatedOnlyFieldListFilter),
                   ('created_on', DateTimeRangeFilter),
                   'ad_orion_node__performance_bucket__name', )
    search_fields = ('ad_node', 'ad_orion_node__node__node_dns',
                     'ad_orion_node__node__node_caption',
                     'ad_orion_node__node__ip_address',)


@admin.register(models.LdapCredError)
class LdapCredErrorAdmin(LdapProbeBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ldap_probe.models.LdapCredError`
    """
    list_display = ('error_unique_identifier', 'enabled',
                    'short_description', 'notes', 'comments', )
    list_editable = ('enabled', 'notes', 'comments', )
    list_filter = ('enabled', )
    search_fields = ('error_unique_identifier', 'short_description', 'notes',
                     'comments', )
