"""
sftp.tasks
----------

This module contains the `Celery tasks
<https://docs.celeryproject.org/en/latest/userguide/tasks.html>`__
used by the :ref:`SFTP monitoring application`.

:copyright:
    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca
"""
import logging

from celery import shared_task
from paramiko import SSHException
import pysftp
from pysftp import ConnectionException

from citrus_borg.dynamic_preferences_registry import get_preference
from p_soc_auto_base.email import Email
from p_soc_auto_base.models import Subscription
from p_soc_auto_base import utils
from sftp.models import SFTPUploadLog

from django.apps import apps

LOG = logging.getLogger(__name__)
"""default :class:`logger.Logging` instance for this module"""


#TODO make sure this is added to app activity list
@shared_task(queue='sftp')
def upload_sftp_file(file, upload_name, host):
    '''
    Uploads a file using sftp to test if the server is available.

    :param file: path to the file to be uploaded
    :param upload_name: location for the file to be uplaoded to
    :param host: address for the server we are connecting to
    '''
    error = ''
    cnopts = pysftp.CnOpts()
    # TODO log message if can't get host names keys

    hostkeys = None

    if cnopts.hostkeys.lookup(host) is None:
        LOG.info("New host - will accept any host key")
        # Backup loaded .ssh/known_hosts file
        hostkeys = cnopts.hostkeys
        # And do not verify host key of the new host
        cnopts.hostkeys = None

    LOG.debug('Trying to connect to %s', host)
    try:
        with pysftp.Connection(host,
                               username=get_preference('sftp__username'),
                               password=get_preference('sftp__password'),
                               cnopts=cnopts)\
                as sftp:
            if hostkeys is not None:
                LOG.info("Connected to new host, caching its hostkey")
                hostkeys.add(host, sftp.remote_server_key.get_name(),
                             sftp.remote_server_key)
                hostkeys.save(pysftp.helpers.known_hosts())
            try:
                sftp.put(file,
                         upload_name)  # upload file to sftp_folder on remote
                LOG.info('File %s successfully uploaded to %s on %s', file,
                         upload_name, host)
            except Exception as exc:  # pylint: disable=broad-except
                # Catch all unexpected exceptions
                # so they will show up in our logs
                LOG.warning('SFTP put failed, %s', exc)
                error = exc
            else:
                sftp.remove(upload_name)
                LOG.info('File %s successfully removed from %s', upload_name,
                         host)
    except SSHException as exc:
        LOG.warning('SSH failed: %s', exc)
        error = exc
    except ConnectionException as exc:
        LOG.warning('SFTP failed, could not connect to %s:%s', exc[0], exc[1])
        error = exc
    except Exception as exc:  # pylint: disable=broad-except
        # Catch all unexpected exceptions so they will show up in our logs
        LOG.warning('Unexpected error encountered: %s %s', type(exc), exc)
        error = exc

    upload_log = SFTPUploadLog(errors=error, host=host)
    upload_log.save()
    if error:
        data = SFTPUploadLog.objects.filter(uuid=upload_log.uuid)
        Email.send_email(data, Subscription.get_subscription('SFTP Alert'),
                         False, host=host)


@shared_task(queue='data_prune')
def delete_sftp_results(**age):
    """
    Deletes SFTP upload logs older than the inputted age

    :arg age: named arguments that can be used for creating a
        :class:`datetime.timedelta` object

        See `Python docs for timedelta objects
        <https://docs.python.org/3.6/library/datetime.html#timedelta
        -objects>`__
    """
    sftp_model = apps.get_model('sftp.SFTPUploadLog')

    older_than = utils.MomentOfTime.past(**age)

    count_deleted = sftp_model.objects.filter(created_on__lte=older_than)\
        .delete()

    LOG.info('Deleted %s sftp logs created earlier than %s.', count_deleted,
             older_than.isoformat())
