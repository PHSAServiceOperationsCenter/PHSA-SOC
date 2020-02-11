"""
.. ssl_admin:

`Django Admin` classes for the :ref:`SSL Certificate Tracker Application`
-------------------------------------------------------------------------

See `The Django admin site
<https://docs.djangoproject.com/en/2.2/ref/contrib/admin/#module-django.contrib.admin>`__.

:module:    p_soc_auto.ssl_cert_tracker.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _
from rangefilter.filter import DateTimeRangeFilter

from p_soc_auto_base.admin import BaseAdmin

from .models import (
    SslExpiresIn, SslHasExpired, SslNotYetValid, Subscription,
    SslCertificate, SslCertificateIssuer, SslProbePort,
)


class SSLCertTrackerBaseAdmin(BaseAdmin, admin.ModelAdmin):
    """
    Base :class:`django.contrib.admin.ModelAdmin` class for all the other
    classes in this module
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        override
        :meth:`django.contrib.admin.ModelAdmin.formfield_for_foreignkey`.

        provide specialized drop-down values for `created_by`, `updated_by`,
        `issuer`, and `port` `ForeignKey` fields.
        """
        if db_field.name in ['created_by', 'updated_by', ]:
            kwargs['queryset'] = get_user_model().objects.\
                filter(username=request.user.username)
            kwargs['initial'] = kwargs['queryset'].get()

        elif db_field.name == 'issuer':
            kwargs['queryset'] = SslCertificateIssuer.active

        elif db_field.name == 'port':
            kwargs['queryset'] = SslProbePort.active

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        """
        override :meth:`django.contrib.admin.ModelAdmin.add_view`.

        pre-populate `created_by` and `updated_by` from the :attr:`user`
        attribute of the `request` object.
        """
        data = request.GET.copy()
        data['created_by'] = request.user
        data['updated_by'] = request.user
        request.GET = data

        return super().add_view(
            request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        override :meth:`django.contrib.admin.ModelAdmin.change_view`

        pre-populate `updated_by` from the :attr:`user` attribute
        of the `request` object.
        """
        data = request.GET.copy()
        data['updated_by'] = request.user
        request.GET = data

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)

    def has_add_permission(self, request):
        """
        override :meth:`django.contrib.admin.has_add_permission`.

        Nobody is allowed to create any instance using forms that inherit from
        this class. All the data is maintained by background processes.
        """
        return False

    def get_readonly_fields(self, request, obj=None):
        """
        override :meth:`django.contrib.admin.ModelAdmin.get_readonly_fields`.

        Make sure that the 'created_by', 'created_on', and 'updated_on' fields
        are always read only.
        """
        if obj is not None:
            return self.readonly_fields + \
                ('created_by', 'created_on', 'updated_on')

        return self.readonly_fields


@admin.register(SslCertificate)
class SslCertificateAdmin(SSLCertTrackerBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ssl_cert_tracker.models.SslCertificate` model
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
        calculated display field showing the trust placed in the certificate
        """
        return obj.issuer.is_trusted
    is_trusted.format_short_description = _('Is Trusted?')


@admin.register(SslCertificateIssuer)
class SslCertificateIssuerAdmin(SSLCertTrackerBaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ssl_cert_tracker.models.SslCertificateIssuer` model
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

    def link_field(self, obj):  # pylint: disable=no-self-use
        """
        calculated field with issuing authority data used on the summary page for
        linking to detail pages
        """
        return 'CN: %s, O: %s' % (obj.common_name, obj.organization_name)
    link_field.short_description = _('Issuing Authority')


@admin.register(SslProbePort)
class SslProbePortAdmin(admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ssl_cert_tracker.models.SslProbePort` model

    .. todo::

        Fix inheritance.
    """
    list_display = ['port', 'enabled', 'updated_on', 'updated_by', ]
    list_edit = ['enabled', ]
    list_filter = ('enabled', ('updated_on', DateTimeRangeFilter),)
    readonly_fields = ('created_on', 'updated_on')

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

    def has_add_permission(self, request):
        """
        override :meth:`django.contrib.admin.has_add_permission`

        Let everybody create :class:`ssl_cert_tracker.models.SslProbePort`
        instances.
        """
        return True


@admin.register(Subscription)
class SubscriptionAdmin(BaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ssl_cert_tracker.models.Subscription` model
    """

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """
        override
        :meth:`django.contrib.admin.ModelAdmin.formfield_for_foreignkey`

        provide specialized drop-down values for `created_by` and `updated_by`.
        """
        if db_field.name in ['created_by', 'updated_by', ]:
            kwargs['queryset'] = get_user_model().objects.\
                filter(username=request.user.username)
            kwargs['initial'] = kwargs['queryset'].get()

        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def add_view(self, request, form_url='', extra_context=None):
        """
        override :meth:`django.contrib.admin.ModelAdmin.add_view`

        pre-populate `created_by` and `updated_by` from the :attr:`user`
        attribute of the `request` object.
        """
        data = request.GET.copy()
        data['created_by'] = request.user
        data['updated_by'] = request.user
        request.GET = data

        return super().add_view(
            request, form_url=form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """
        override :meth:`django.contrib.admin.ModelAdmin.change_view`

        Pre-populate `updated_by` from the :attr:`user` attribute of the
        `request` object.
        """
        data = request.GET.copy()
        data['updated_by'] = request.user
        request.GET = data

        return super().change_view(
            request, object_id, form_url=form_url, extra_context=extra_context)

    def get_readonly_fields(self, request, obj=None):
        """
        override :meth:`django.contrib.admin.ModelAdmin.get_readonly_fields`

        Make sure that the 'created_by', 'created_on', and 'updated_on' fields
        are always read only.

        .. todo::

            This method may be a duplicate and/or redundant.
        """
        if obj is not None:
            return self.readonly_fields + \
                ('created_by', 'created_on', 'updated_on')

        return self.readonly_fields

    def has_add_permission(self, request):
        """
        override :meth:`django.contrib.admin.has_add_permission`.

        Only a `superuser
        <https://docs.djangoproject.com/en/2.2/ref/contrib/auth/#django.contrib.auth.models.User.is_superuser>`__
        can create :class:`ssl_cert_tracker.models.Subscription` instances using
        this form
        """
        if request.user.is_superuser:
            return True

        return False

    def has_delete_permission(self, request, obj=None):
        """
        override :meth:`django.contrib.admin.has_delete_permission`

        Only a `superuser
        <https://docs.djangoproject.com/en/2.2/ref/contrib/auth/#django.contrib.auth.models.User.is_superuser>`__
        can delete :class:`ssl_cert_tracker.models.Subscription` instances using
        this form
        """
        if request.user.is_superuser:
            return True

        return False

    list_display = ['subscription', 'enabled', 'emails_list', 'template_dir',
                    'template_name', 'template_prefix', 'updated_on',
                    'updated_by']
    list_editable = ['enabled', 'emails_list', 'template_dir',
                     'template_name', 'template_prefix']
    readonly_fields = ('created_on', 'updated_on', )
    list_filter = ('enabled', )
    search_fields = ('subscription', )


@admin.register(SslExpiresIn)
class SslExpiresInAdmin(SslCertificateAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ssl_cert_tracker.models.SslExpiresIn` model
    """
    readonly_fields = ('expires_in_days',)
    list_display = ['common_name', 'organization_name', 'enabled',
                    'expires_in_days',
                    'not_before', 'not_after', 'node_admin_url',
                    'orion_node_url', 'updated_on']

    def expires_in_days(self, obj):
        return obj.expires_in_x_days
    expires_in_days.short_description = 'expires in X days'


@admin.register(SslHasExpired)
class SslHasExpiredAdmin(SslCertificateAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ssl_cert_tracker.models.SslHasExpired` model
    """
    readonly_fields = ('has_expired_days_ago',)
    list_display = ['common_name', 'organization_name', 'enabled',
                    'has_expired_days_ago',
                    'not_before', 'not_after', 'node_admin_url',
                    'orion_node_url', 'updated_on']

    def has_expired_days_ago(self, obj):
        return obj.has_expired_x_days_ago
    has_expired_days_ago.short_description = 'has expired X days ago'


@admin.register(SslNotYetValid)
class SslNotYetValidAdmin(SslCertificateAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`ssl_cert_tracker.models.SslNotYetValid` model
    """
    readonly_fields = ('valid_in_days',)
    list_display = ['common_name', 'organization_name', 'enabled',
                    'valid_in_days',
                    'not_before', 'not_after', 'node_admin_url',
                    'orion_node_url', 'updated_on']

    def valid_in_days(self, obj):
        return obj.will_become_valid_in_x_days
    valid_in_days.short_description = 'will become valid in X days'
