"""
.. sftp.models:

Django models for the sftp app

:copyright:

    Copyright 2020 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from p_soc_auto_base.utils import get_uuid


class SFTPUploadLog(models.Model):
    """
    :class:`django.db.models.Model` class used for storing SFTP test
    information
    """
    uuid = models.UUIDField(_('UUID'), unique=True, db_index=True, blank=False,
                            null=False, default=get_uuid)
    errors = models.TextField(_('Errors'), blank=True, null=True)
    created_on = models.DateTimeField(_('created on'), db_index=True,
        auto_now_add=True, help_text=_('object creation time stamp'))
    host = models.TextField(_('Host'), blank=False, null=False)
