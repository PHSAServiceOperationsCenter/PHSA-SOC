"""
.. _admin:

django admin module for the orion_flash app

:module:    p_soc_auto.orion_flash.admin

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Feb. 20, 2019

"""
from django.utils.safestring import mark_safe
from django.contrib import admin

from .models import (
    UntrustedSslAlert, ExpiresSoonSslAlert, ExpiredSslAlert, InvalidSslAlert,
)


class BaseSslAlertAdmin(admin.ModelAdmin):
    """
    parent class for the admin classes defined in this module
    """
    actions = None
    list_display = ('cert_subject', 'md5', 'orion_node_id', 'orion_node_port',
                    'silenced', 'alert_body', 'show_cert_url')
    list_editable = ('silenced',)

    readonly_fields = ('show_cert_url',)

    def has_add_permission(self, request):  # @UnusedVariable
        """
        instances of these models are created by background processes
        based on data collected from various sources.

        therefore adding instances from the admin interface is not allowed
        """
        return False

    def has_delete_permission(self, request, obj=None):  # @UnusedVariable
        """
        instances of these models are maintained by background processes.

        deleting from the admin interface is not allowed
        """
        return False

    def get_readonly_fields(self, request, obj=None):  # @UnusedVariable
        """
        all the fields on these forms need to be read only with the
        exception of the 'silenced' field
        """
        return self.readonly_fields + \
            tuple([field.name for field in obj._meta.fields
                   if field.name != 'silenced'])

    def show_cert_url(self, obj):  # pylint: disable=no-self-use
        """
        render the link to the SSL certificate admin page as an URL
        """
        return mark_safe('<a href="{0}">{0}</a>'.format(obj.cert_url))
    show_cert_url.short_description = 'SSL Certificate URL'


@admin.register(UntrustedSslAlert)
class UntrustedSslAlertAdmin(BaseSslAlertAdmin, admin.ModelAdmin):
    """
    admin interface for alerts about untrusted SSL certificates
    """

    def get_list_display(self, request):  # @UnusedVariable
        """
        override the list_display attribute with specific fields
        """
        return self.list_display + ('cert_issuer',)


@admin.register(ExpiresSoonSslAlert)
class ExpiresSoonSslAlertAdmin(BaseSslAlertAdmin, admin.ModelAdmin):
    """
    admin interface for alerts about SSL certificates that expire soon
    """

    def show_expires_in(self, obj):  # pylint: disable=no-self-use
        """
        append 'days' to the value of expires_in
        """
        days = 'days'

        if obj.expires_in == 1:
            days = 'day'

        return '{} {}'.format(obj.expires_in, days)
    show_expires_in.short_description = 'Will expire in'

    def get_list_display(self, request):  # @UnusedVariable
        """
        override the list_display attribute with specific fields
        """
        return self.list_display + ('show_expires_in', 'not_after')


@admin.register(ExpiredSslAlert)
class ExpiredSslAlertAdmin(BaseSslAlertAdmin, admin.ModelAdmin):
    """
    admin forms for alerts about expired SSL certificates
    """

    def show_has_expired(self, obj):  # pylint: disable=no-self-use
        """
        pretty has expired x days ago
        """
        days = 'days'

        if obj.has_expired == 1:
            days = 'day'

        return '{} {} ago'.format(obj.has_expired, days)
    show_has_expired.short_description = 'Has expired'

    def get_list_display(self, request):  # @UnusedVariable
        """
        override the list_display attribute with specific fields
        """
        return self.list_display + ('cert_issuer', 'show_has_expired',
                                    'not_after')


@admin.register(InvalidSslAlert)
class InvalidSslAlertAdmin(BaseSslAlertAdmin, admin.ModelAdmin):
    """
    admin forms for alerts about SSL certificates that are not yet valid
    """

    def show_not_yet_valid(self, obj):  # pylint: disable=no-self-use
        """
        pretty has expired x days ago
        """
        days = 'days'

        if obj.invalid_for == 1:
            days = 'day'

        return '{} {} ago'.format(obj.invalid_for, days)
    show_not_yet_valid.short_description = 'Will not be valid for another'

    def get_list_display(self, request):  # @UnusedVariable
        """
        override the list_display attribute with specific fields
        """
        return self.list_display + ('cert_issuer', 'show_not_yet_valid',
                                    'not_before')
