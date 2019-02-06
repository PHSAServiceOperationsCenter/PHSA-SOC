from django.contrib import admin

from .models import (
    UntrustedSslAlert, ExpiresSoonSslAlert, ExpiredSslAlert, InvalidSslAlert,
)


@admin.register(UntrustedSslAlert)
class UntrustedSslAlertAdmin(admin.ModelAdmin):
    pass


@admin.register(ExpiresSoonSslAlert)
class ExpiresSoonSslAlertAdmin(admin.ModelAdmin):
    pass


@admin.register(ExpiredSslAlert)
class ExpiredSslAlertAdmin(admin.ModelAdmin):
    pass


@admin.register(InvalidSslAlert)
class InvalidSslAlertAdmin(admin.ModelAdmin):
    pass
