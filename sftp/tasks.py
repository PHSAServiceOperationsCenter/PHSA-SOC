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
from sftp.models import SFTPUploadLog

LOG = logging.getLogger(__name__)
"""default :class:`logger.Logging` instance for this module"""


@shared_task(queue='sftp')
def upload_sftp_file(sftp_path, file, host):
    '''
    Uploads a file using sftp to test if the server is available.

    :param sftp_path: where the file is stored on the SFTP server
    :param file: path to the file to be uploaded
    :param host: address for the server we are connecting to
    '''
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
            with sftp.cd(sftp_path):  # temporarily chdir to sftp_path
                error = ''
                try:
                    sftp.put(file)  	  # upload file to sftp_folder on remote
                    LOG.info('File %s successfully uploaded to %s', file, host)
                except Exception as exc:  # pylint: disable=broad-except
                    # Catch all unexpected exceptions
                    # so they will show up in our logs
                    LOG.warning('SFTP put failed, %s', exc)
                    error = exc
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
