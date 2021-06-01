"""
.. sftp.models:

Django models for the :ref:`SFTP monitoring application`
--------------------------------------------------------

:copyright:

    Copyright 2020 Provincial Health Service Authority
    of British Columbia

"""

from django.db import models
from django.utils.decorators import classproperty
from django.utils.translation import gettext_lazy as _

from p_soc_auto_base.models import BaseModel


class SFTPUploadLog(BaseModel):
    """
    :class:`django.db.models.Model` class used for storing SFTP test
           information
    """
    errors = models.TextField(_('Errors'), blank=True, null=True)
    host = models.TextField(_('Host'), blank=False, null=False)

    @classproperty
    def gen_func_name(self):
        return 'upload_sftp_file'

    class Meta:
        app_label = 'sftp'
        verbose_name = _('SFTP Upload Log')
        get_latest_by = 'created'
        ordering = ['-created']
