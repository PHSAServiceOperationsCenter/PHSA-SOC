"""
.. _tasks:

celery tasks for the orion_flash app

:module:    orion_flash.tasks

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Feb. 1, 2019

"""
from django.apps import apps

from celery import shared_task, group  # @UnresolvedImport
from celery.utils.log import get_task_logger  # @UnresolvedImport


from p_soc_auto_base.utils import get_pk_list  # @UnresolvedImport
from ssl_cert_tracker.lib import (
    is_not_trusted, expires_in, has_expired, is_not_yet_valid,  # @UnresolvedImport
)


LOG = get_task_logger(__name__)


@shared_task(rate_limit='2/s', queue='orion_flash')
def update_or_create_orion_alert(dest_name, source_pk):
    """
    create orion auxiliary alert instances
    """
    try:
        return apps.get_model(dest_name).create(source_pk)
    except Exception as err:
        raise err


@shared_task(queue='orion_flash_dispatch')
def refresh_ssl_untrusted_alerts():
    """
    dispatch alert data to orion auxiliary alert models
    """
    dest_name = 'orion_flash.ssluntrustedauxalert'
    source_pks = get_pk_list(is_not_trusted())

    group(update_or_create_orion_alert.s(dest_name, source_pk)
          for source_pk in source_pks)()

    msg = ('dispatched %s untrusted'
           ' SSL certificate alerts') % len(source_pks)
    return msg
