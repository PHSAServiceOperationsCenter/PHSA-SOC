"""
.. sftp_admin:

:module:    sftp.admin

:copyright:

    Copyright 2020 Provincial Health Service Authority of British Columbia

:contact:    daniel.busto@phsa.ca

"""

from django.contrib import admin

from p_soc_auto_base.admin import BaseAdmin
from .models import SFTPUploadLog


@admin.register(SFTPUploadLog)
class SFTPUploadAdmin(BaseAdmin, admin.ModelAdmin):
    """
    :class:`django.contrib.admin.ModelAdmin` class for the
    :class:`SFTPUploadLog` model
    """
    list_display = ['created_on', 'host', 'errors', ]
    list_filter = ['host', 'errors']
