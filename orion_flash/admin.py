"""
.. _admin:

django admin module for the orion_flash app

:module:    p_soc_auto.orion_flash.admin

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

:updated:    Feb. 20, 2019

"""
import pendulum

from django.utils.safestring import mark_safe
from django.contrib import admin

from .models import (
    UntrustedSslAlert, ExpiresSoonSslAlert, ExpiredSslAlert, InvalidSslAlert,
    DeadCitrusBotAlert, CitrusBorgLoginAlert, CitrusBorgUxAlert,
)


class BaseAlertAdmin(admin.ModelAdmin):
    """
    parent class for all classes in this module
    """

    list_editable = ('silenced',)

    def has_add_permission(self, request):  # @UnusedVariable
        """
        instances of these models are created by background processes
        based on data collected from various sources.

        therefore adding instances from the admin interface is not allowed
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


class BorgAlertAdmin(BaseAlertAdmin, admin.ModelAdmin):
    """
    parent class for admin classes used for borg alerts
    """
    list_display = ('host_name', 'site', 'orion_node_id', 'alert_body',
                    'silenced', 'measured_now', 'show_time_delta',
                    'show_bot_url', 'show_events_url',)
    readonly_fields = ('show_time_delta', 'show_bot_url', 'show_events_url',)

    def show_time_delta(self, obj):  # pylint: disable=no-self-use
        """
        combine and display the time delta
        :param obj:
        :type obj:
        """
        return pendulum.duration(
            days=obj.measured_over.days, seconds=obj.measured_over.seconds,
            microseconds=obj.measured_over.microseconds).\
            in_words()
    show_time_delta.short_description = 'Duration Going Backwards'

    def show_bot_url(self, obj):  # pylint: disable=no-self-use
        """
        render the link to the Citrix bot admin page as an URL
        """
        return mark_safe('<a href="{0}">{0}</a>'.format(obj.bot_url))
    show_bot_url.short_description = 'Citrix bot details'

    def show_events_url(self, obj):  # pylint: disable=no-self-use
        """
        render the link to the Citrix bot events admin page as an URL
        """
        return mark_safe('<a href="{0}">{0}</a>'.format(obj.events_url))
    show_events_url.short_description = 'Citrix bot events summary'


class SslAlertAdmin(BaseAlertAdmin, admin.ModelAdmin):
    """
    parent class for the admin classes used for ssl alerts
    """
    list_display = ('cert_subject', 'md5', 'orion_node_id', 'orion_node_port',
                    'silenced', 'alert_body', 'show_cert_url')
    readonly_fields = ('show_cert_url',)

    def show_cert_url(self, obj):  # pylint: disable=no-self-use
        """
        render the link to the SSL certificate admin page as an URL
        """
        return mark_safe('<a href="{0}">{0}</a>'.format(obj.cert_url))
    show_cert_url.short_description = 'SSL Certificate URL'


@admin.register(DeadCitrusBotAlert)
class DeadCitrusBotAlertAdmin(BorgAlertAdmin, admin.ModelAdmin):
    """
    admin interface for alerts about dead citrix bots
    """

    def get_list_display(self, request):  # @UnusedVariable
        """
        add our fields to the list_display
        """
        return self.list_display + ('not_seen_for',)


@admin.register(CitrusBorgLoginAlert)
class CitrusBorgLoginAlertAdmin(BorgAlertAdmin, admin.ModelAdmin):
    """
    admin interface for alerts about missed citrix logins
    """

    def get_list_display(self, request):
        """
        add our fields to the list_display
        """
        return self.list_display + ('failed_events_count',)


@admin.register(CitrusBorgUxAlert)
class CitrusBorgUxAlertAdmin(BorgAlertAdmin, admin.ModelAdmin):
    """
    admin interface for alerts about citrix bot response time events
    """

    def get_list_display(self, request):
        """
        add our fields to the list_display
        """
        return self.list_display + (
            'avg_logon_time', 'avg_storefront_connection_time',)


@admin.register(UntrustedSslAlert)
class UntrustedSslAlertAdmin(SslAlertAdmin, admin.ModelAdmin):
    """
    admin interface for alerts about untrusted SSL certificates
    """

    def get_list_display(self, request):  # @UnusedVariable
        """
        override the list_display attribute with specific fields
        """
        return self.list_display + ('cert_issuer',)


@admin.register(ExpiresSoonSslAlert)
class ExpiresSoonSslAlertAdmin(SslAlertAdmin, admin.ModelAdmin):
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
class ExpiredSslAlertAdmin(SslAlertAdmin, admin.ModelAdmin):
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
class InvalidSslAlertAdmin(SslAlertAdmin, admin.ModelAdmin):
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
