"""
.. _admin:

django admin for the ssl_cert_tracker app

:module:    p_soc_auto.ssl_cert_tracker.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

:updated:    sep. 21, 2018
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter

from simple_history.admin import SimpleHistoryAdmin

from p_soc_auto_base.admin import BaseAdmin

from .models import (
    NmapCertsData, SslExpiresIn, SslHasExpired, SslNotYetValid, Subscription,
    SslCertificate, SslCertificateIssuer, SslProbePort,
)


class SSLCertTrackerBaseAdmin(BaseAdmin, admin.ModelAdmin):
    """
    base class for admin classes in this application
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        overload
        admin.ModelAdmin.formfield_for_foreignkey(
            self, db_field, request, **kwargs)
        """
        if db_field.name in ['created_by', 'updated_by', ]:
            kwargs['queryset'] = get_user_model().objects.\
                filter(username=request.user.username)
            kwargs['initial'] = kwargs['queryset'].get()

        if db_field.name in ['issuer', ]:
            kwargs['queryset'] = SslCertificateIssuer.objects.filter(
                enabled=True)

        if db_field.name in ['port', ]:
            kwargs['queryset'] = SslProbePort.objects.filter(
                enabled=True)

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        """
        overload to populate the user fields from the request object
        """
        data = request.GET.copy()
        data['created_by'] = request.user
        data['updated_by'] = request.user
        request.GET = data

        return super().add_view(
            request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        overload to populate updated_by from the request object
        """
        data = request.GET.copy()
        data['updated_by'] = request.user
        request.GET = data

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)

    def has_add_permission(self, request, obj=None):
        """
        all these things are populated from orion

        do not allow any tom, dick, and harriet to add stuff on their own
        """
        return False

    def get_readonly_fields(self, request, obj=None):
        """
        overload to make sure that some fields are always readonly
        """
        if obj is not None:
            return self.readonly_fields + \
                ('created_by', 'created_on', 'updated_on')

        return self.readonly_fields


@admin.register(SslCertificate)
class SslCertificateAdmin(SSLCertTrackerBaseAdmin, admin.ModelAdmin):
    """
    admin forms for SSL certificates
    """
    list_display = ['common_name', 'organization_name',
                    'country_name', 'enabled', 'is_trusted', 'port',
                    'pk_bits', 'node_admin_url',
                    'orion_node_url', 'not_before', 'not_after', 'last_seen']
    list_editable = ['enabled', ]
    readonly_fields = ('common_name', 'organization_name', 'pk_bits',
                       'country_name', 'node_admin_url', 'orion_node_url',
                       'not_before', 'not_after', 'last_seen', 'is_trusted',)
    list_filter = ('enabled',  'organization_name',
                   ('last_seen', DateTimeRangeFilter),
                   ('updated_on', DateTimeRangeFilter),)
    search_fields = ['common_name',
                     'organization_name', 'country_name', 'notes', ]

    fieldsets = (
        ('Identification', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('enabled', 'last_seen'),
                       ('common_name', 'organization_name',
                        'country_name', ), ('issuer', 'is_trusted', ), ),
        }, ),
        ('Node Info', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('port', 'node_admin_url', 'orion_node_url', ), ),
        }, ),
        ('Validity', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('not_before', 'not_after'), ),
        }, ),
        ('Private Key Info', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('pk_bits', 'pk_type'), ('pk_md5', ), ('pk_sha1', ), ),
        }, ),
        ('PEM (+/-)', {
            'classes': ('grp-collapse grp-open', ),
            'fields': ('pem', ),
        }, ),
        ('Description (+/-)', {
            'classes': ('grp-collapse grp-open', ),
            'fields': ('notes', ),
        }, ),
        ('History (+/-)', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': (('created_on', 'created_by', ),
                       ('updated_on', 'updated_by', ),),
        }, ),
    )

    def is_trusted(self, obj):
        """
        is this a trusted certificate
        """
        return obj.issuer.is_trusted
    is_trusted.format_short_description = _('Is Trusted?')


@admin.register(SslCertificateIssuer)
class SslCertificateIssuerAdmin(SSLCertTrackerBaseAdmin, admin.ModelAdmin):
    """
    admin forms for SSL certificate issuers
    """
    list_display = ['link_field', 'common_name', 'organization_name',
                    'country_name', 'enabled', 'is_trusted']
    list_editable = ['enabled', 'is_trusted']
    readonly_fields = ('link_field', 'common_name', 'organization_name',
                       'country_name')
    list_filter = ('enabled', 'is_trusted', 'organization_name',
                   ('updated_on', DateTimeRangeFilter),)
    search_fields = ['common_name',
                     'organization_name', 'country_name', 'notes', ]

    fieldsets = (
        ('Identification', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('enabled', 'is_trusted',),
                       ('common_name', 'organization_name',
                        'country_name', ), ),
        }, ),
        ('Description (+/-)', {
            'classes': ('grp-collapse grp-open', ),
            'fields': ('notes', ),
        }, ),
        ('History (+/-)', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': (('created_on', 'created_by', ),
                       ('updated_on', 'updated_by', ),),
        }, ),
    )

    def link_field(self, obj):
        """
        link on something that is never empty
        """
        return 'CN: %s, O: %s' % (obj.common_name, obj.organization_name)
    link_field.short_description = _('Issuing Authority')


@admin.register(SslProbePort)
class SslProbePortAdmin(SSLCertTrackerBaseAdmin, admin.ModelAdmin):
    """
    admin forms for SSL scanning ports
    """
    list_display = ['port', 'enabled', 'updated_on', 'updated_by', ]
    list_edit = ['enabled', ]
    list_filter = ('enabled', ('updated_on', DateTimeRangeFilter),)

    fieldsets = (
        ('Identification', {
            'classes': ('extrapretty', 'wide', ),
            'fields': (('enabled', 'port',), ),
        }, ),
        ('Description (+/-)', {
            'classes': ('grp-collapse grp-open', ),
            'fields': ('notes', ),
        }, ),
        ('History (+/-)', {
            'classes': ('grp-collapse grp-closed', ),
            'fields': (('created_on', 'created_by', ),
                       ('updated_on', 'updated_by', ),),
        }, ),
    )

    def has_add_permission(self, request, obj=None):
        """
        revert the overload from the base class
        """
        return True


@admin.register(Subscription)
class SubscriptionAdmin(BaseAdmin, admin.ModelAdmin):
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        overload
        admin.ModelAdmin.formfield_for_foreignkey(
            self, db_field, request, **kwargs)
        """
        if db_field.name in ['created_by', 'updated_by', ]:
            kwargs['queryset'] = get_user_model().objects.\
                filter(username=request.user.username)
            kwargs['initial'] = kwargs['queryset'].get()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        """
        overload to populate the user fields from the request object
        """
        data = request.GET.copy()
        data['created_by'] = request.user
        data['updated_by'] = request.user
        request.GET = data

        return super().add_view(
            request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        overload to populate updated_by from the request object
        """
        data = request.GET.copy()
        data['updated_by'] = request.user
        request.GET = data

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)

    def get_readonly_fields(self, request, obj=None):
        """
        overload to make sure that some fields are always readonly
        """
        if obj is not None:
            return self.readonly_fields + \
                ('created_by', 'created_on', 'updated_on')

        return self.readonly_fields

    def has_add_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        return False

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True

        return False

    list_display = ['subscription', 'enabled', 'emails_list', 'template_dir',
                    'template_name', 'template_prefix', 'updated_on',
                    'updated_by']
    list_editable = ['enabled', 'emails_list', 'template_dir',
                     'template_name', 'template_prefix']
    readonly_fields = ('created_on', 'updated_on', )


@admin.register(NmapCertsData)
class NmapCertsDataAdmin(SSLCertTrackerBaseAdmin, SimpleHistoryAdmin):
    """
    SSL certificate data admin pages
    """
    list_display = ['common_name', 'organization_name', 'not_before',
                    'not_after', 'node_admin_url', 'orion_node_url',
                    'updated_on']
    history_list_display = ['updated_on', ]
    list_filter = [('not_after', DateRangeFilter),
                   ('not_before', DateRangeFilter),
                   ('updated_on', DateRangeFilter)]
    search_fields = ['common_name', 'organization_name']
    readonly_fields = ['node_admin_url', 'orion_node_url', ]


@admin.register(SslExpiresIn)
class SslExpiresInAdmin(NmapCertsDataAdmin):
    """
    only valid SSL certificates sorted by expiration date ascending
    """
    readonly_fields = ('expires_in_days',)
    list_display = ['common_name', 'organization_name', 'expires_in_days',
                    'not_before', 'not_after', 'node_admin_url',
                    'orion_node_url', 'updated_on']

    def expires_in_days(self, obj):
        return obj.expires_in_x_days
    expires_in_days.short_description = 'expires in X days'


@admin.register(SslHasExpired)
class SslHasExpiredAdmin(NmapCertsDataAdmin):
    """
    only expired SSL certificates sorted by expiration date ascending
    """
    readonly_fields = ('has_expired_days_ago',)
    list_display = ['common_name', 'organization_name',
                    'has_expired_days_ago',
                    'not_before', 'not_after', 'node_admin_url',
                    'orion_node_url', 'updated_on']

    def has_expired_days_ago(self, obj):
        return obj.has_expired_x_days_ago
    has_expired_days_ago.short_description = 'has expired X days ago'


@admin.register(SslNotYetValid)
class SslNotYetValiddAdmin(NmapCertsDataAdmin):
    """
    only not yet valid SSL certificates sorted by expiration date ascending
    """
    readonly_fields = ('valid_in_days',)
    list_display = ['common_name', 'organization_name',
                    'valid_in_days',
                    'not_before', 'not_after', 'node_admin_url',
                    'orion_node_url', 'updated_on']

    def valid_in_days(self, obj):
        return obj.will_become_valid_in_x_days
    valid_in_days.short_description = 'will become valid in X days'
