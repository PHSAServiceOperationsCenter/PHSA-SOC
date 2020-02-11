"""
.. _ssl_cert_tracker_tasks:

Celery tasks for the :ref:`SSL Certificate Tracker Application`
---------------------------------------------------------------

:module:    ssl_cert_tracker.tasks

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from smtplib import SMTPConnectError

from celery import shared_task, group
from celery.utils.log import get_task_logger

from orion_integration.lib import OrionSslNode
from orion_integration.models import OrionNode

from .lib import Email, expires_in, has_expired, is_not_yet_valid
from .models import Subscription, SslProbePort, SslCertificate
from .nmap import (
    SslProbe, NmapError, NmapHostDownError, NmapNotAnSslNodeError,
)


LOG = get_task_logger(__name__)
"""
fall-back logging object for this module

All the functions and methods in this module will use this `Logger` instance
if they are not called with a `logger` argument.
"""


class OrionDataError(Exception):
    """
    Custom :exc:`Exception` class raises when there are no `Orion
    <https://www.solarwinds.com/solutions/orion>`__ nodes available
    for `NMAP <https://nmap.org/>`_
    """


@shared_task(
    queue='ssl', rate_limit='1/s', max_retries=3,
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_ssl_report():
    """
    task to send `SSL` reports via email

    In this task, the data contains all the valid `SSL` certificates ordered
    by the number of days left until they expire.

    We could make this a more abstract task but then:

    * We would have to use :mod:`pickle` to serialize a `Django`
      :class:`django.db.models.query.QuerySet` to a `Celery task
      <https://docs.celeryproject.org/en/latest/userguide/tasks.html#tasks>`__.
      This is not the default and it does have security implications

    * We would also have to train the users on how to configure `Periodic tasks
      <https://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#periodic-tasks>`__
      using `django-celery-beat
      <https://docs.celeryproject.org/en/latest/userguide/periodic-tasks.html#using-custom-scheduler-classes>`__

    * See :func:`mail_collector.tasks.bring_out_your_dead` for an example about
      a complex, abstract task. The user also has to understand how to write
      `JSON <https://www.json.org/>`__ data by hand in order to configure
      different `Periodic tasks` wrapped around this task by hand

    This, and all the other tasks, dealing with `SSL` reports and alerts follow
    the recommended patterns for basic `Celery` tasks.

    """
    return Email.send_email(
        data=expires_in(),
        subscription_obj=Subscription.objects.get(
            subscription='SSl Report'))


@shared_task(
    queue='ssl', rate_limit='1/s', max_retries=3,
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_ssl_expires_in_days_report(lt_days):  # pylint: disable=invalid-name
    """
    task to send email alerts about `SSL` certificated that will expire soon

    :arg int lt_days: the alarm trigger

        Raise an alert for each `SSL` certificate that will expired in fewer
        days than the number provided by this argument.

    """
    return Email.send_email(
        data=expires_in(lt_days=lt_days),
        subscription_obj=Subscription.objects.get(subscription='SSl Report'),
        expires_in_less_than=lt_days)


@shared_task(
    queue='ssl', rate_limit='1/s', max_retries=3,
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_expired_ssl_report():
    """
    task to send reports about expired `SSL` by email

    """
    return Email.send_email(
        data=has_expired(),
        subscription_obj=Subscription.objects.get(
            subscription='Expired SSl Report'), expired=True)


@shared_task(
    queue='ssl', rate_limit='1/s', max_retries=3,
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_invalid_ssl_report():
    """
    task to send reports about `SSL` certificates that are not yet valid by
    email

    """
    return Email.send_email(
        data=is_not_yet_valid(),
        subscription_obj=Subscription.objects.get(
            subscription='Invalid SSl Report'), invalid=True)


@shared_task(task_serializer='pickle', rate_limit='5/s', queue='shared')
def get_ssl_for_node(orion_node):
    """
    task that spawns separate :func:`get_ssl_for_node_port` tasks for each
    network port to be probed on a given :class:`Orion node
    <orion_integration.models.OrionNode>`

    The list of network ports is collected from the
    :class:`ssl_cert_tracker.models.SslProbePort` models, specifically all the
    instances of this model that are `enabled`.

    :arg orion_node: the :class:`orion_integration.models.OrionNode` instance

    :returns: the :attr:`orion_integration.models.OrionNode.node_caption` and
        a list of ports to be probed
    :rtype: str
    """
    ssl_ports = SslProbePort.active.all()

    group(get_ssl_for_node_port.
          s(orion_node, ssl_port).
          set(serializer='pickle') for ssl_port in ssl_ports)()

    LOG.info('looking for SSL certificates on Orion node %s (%s), ports %s',
             orion_node.node_caption, orion_node.ip_address,
             ', '.join(str(ssl_ports.values_list('port', flat=True))))


@shared_task(task_serializer='pickle', rate_limit='2/s', queue='nmap',
             autoretry_for=(NmapError, NmapHostDownError),
             max_retries=3, retry_backoff=True)
def get_ssl_for_node_port(orion_node, port):
    """
    this task is a wrapper around an :class:`ssl_cert_tracker.nmap.SslProbe`
    `NMAP <https://nmap.org/>`__ `SSL
    <https://en.wikipedia.org/wiki/Public_key_certificate#TLS/SSL_server_certificate>`__
    scan

    :arg orion_node: the :class:`<orion_integration.models.OrionNode>` instance

    :arg int port: the network port for the scan

    :returns: the `SSL` certificate subject, the `SSL` certificate host names,
        the `SSL` certificate port, and the date when the certificate was
        created or updated
    :rtype: str
    """
    try:
        ssl_certificate = SslProbe(orion_node.ip_address, port)
    except NmapNotAnSslNodeError:
        LOG.warning('there is no SSL certificate on %s:%s',
                    orion_node.ip_address, port)
        return

    LOG.debug('nmap returned %s', ssl_certificate.summary)

    created, ssl_obj = SslCertificate.create_or_update(orion_node.orion_id,
                                                       ssl_certificate)

    if created:
        LOG.info('SSL certificate %s on %s, port %s has been created at %s',
                 ssl_certificate.ssl_subject, ssl_certificate.hostnames,
                 ssl_certificate.port, ssl_obj.created_on)
        return

    LOG.info('SSL certificate %s on %s, port %s last seen at %s',
             ssl_certificate.ssl_subject, ssl_certificate.hostnames,
             ssl_certificate.port, ssl_obj.last_seen)


@shared_task(rate_limit='2/s', queue='nmap',
             autoretry_for=(NmapError, NmapHostDownError),
             max_retries=3, retry_backoff=True)
def verify_ssl_for_node_port(cert_node_port_tuple):
    """
    task that verifies the existence of an `SSL` certificate know to us on the
    network.

    This task will run a :class:`ssl_cert_tracker.nmap.SslProbe`
    `NMAP <https://nmap.org/>`__ `SSL
    <https://en.wikipedia.org/wiki/Public_key_certificate#TLS/SSL_server_certificate>`__
    scan for an :class:`ssl_cert_tracker.models.SslCertificate` instance
    represented by a (:class:`orion_integration.models.OrionNode`, network port)
    tuple.
    If the `SSL` certificate is not found during the scan, the corresponding
    :class:`ssl_cert_tracker.models.SslCertificate` instance will be deleted.

    :arg tuple cert_node_port_tuple:

        a (:class:`orion_integration.models.OrionNode`, network port) tuple

    :returns: a :class:`str` with the result of the verification
    """
    port = cert_node_port_tuple[2]

    try:
        ip_address = OrionNode.objects.get(
            orion_id=cert_node_port_tuple[1]).ip_address
    except OrionNode.DoesNotExist:
        SslCertificate.objects.filter(
            orion_id=cert_node_port_tuple[1]).all().delete()
        LOG.info('Deleted orphan SSL certificate on %s:%s. Orion node with id'
                 ' %s does not exist', cert_node_port_tuple[1], port,
                 cert_node_port_tuple[1])

    try:
        _ = SslProbe(ip_address, port)
    except NmapNotAnSslNodeError:
        SslCertificate.objects.filter(
            id=cert_node_port_tuple[0]).delete()
        LOG.info('there is no SSL certificate on %s:%s. Removing this'
                 ' certificate from the database', ip_address, port)
        return

    LOG.info('found an SSL certificate on %s:%s.', ip_address, port)


@shared_task(queue='shared')
def verify_ssl_certificates():
    """
    task that spawns a :func:`verify_ssl_for_node_port` task for each `enabled`
    :class:`ssl_cert_tracker.models.SslCertificate` instance

    :returns: the number of `SSL` certificates that will be verified
    :rtype: str
    """
    cert_node_port_list = SslCertificate.active.\
        values_list('id', 'orion_id', 'port__port')

    group(verify_ssl_for_node_port.s(cert_node_port_tuple) for
          cert_node_port_tuple in cert_node_port_list)()

    LOG.info('verifying %s known SSL certificates against Orion nodes',
             len(cert_node_port_list))


@shared_task(queue='shared')
def get_ssl_nodes():
    """
    task that spawns a :func:`get_ssl_for_node` task for each
    :class:`orion_integration.models.OrionNode` instance known to serve `SSL`
    certificates

    :returns: the number of :class:`Orion nodes
        <orion_integration.models.OrionNode>` that will be inspected
    :rtype: str
    """
    orion_nodes = OrionSslNode.nodes()
    if not orion_nodes:
        raise OrionDataError(
            'there are no Orion nodes available for SSL nmap probing')

    group(get_ssl_for_node.s(orion_node).set(serializer='pickle') for
          orion_node in orion_nodes)()

    LOG.info('looking for SSL certificates on %s Orion nodes', len(orion_nodes))
