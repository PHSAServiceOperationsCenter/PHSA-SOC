"""
.. _tasks:

celery tasks for the ssl_certificates app

:module:    ssl_cert_tracker.tasks

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca
:contact:    serban.teodorescu@phsa.ca

:updated: Nov. 22, 2018

"""
from smtplib import SMTPConnectError
import xml.dom.minidom

from celery import shared_task, group
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from libnmap.process import NmapProcess

from orion_integration.lib import OrionSslNode
from orion_integration.models import OrionNode

from .lib import Email, expires_in, has_expired, is_not_yet_valid
from .models import Subscription, SslProbePort, SslCertificate
from .nmap import (
    SslProbe, NmapError, NmapHostDownError, NmapNotAnSslNodeError,
)


LOG = get_task_logger(__name__)

SSL_PROBE_OPTIONS = r'-Pn -p 443 --script ssl-cert'


class NmapXMLError(Exception):
    """
    raise when the XML report from nmap cannot be processed
    """


class NoSSLCertOnNodeError(Exception):
    """
    raise if there is no SSL certificate on the node probed by nmap
    """


class SSLDatabaseError(Exception):
    """
    raise if one cannot update the database with the SSL certificate
    collected with nmap
    """


class OrionDataError(Exception):
    """
    raise when there are no orion nodes available for nmap probing
    """


@shared_task(
    queue='ssl', rate_limit='1/s', max_retries=3,
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_ssl_report():
    """
    task to send ssl reports via email

    we could make this a more abstract email_report task but then we would
    have to deal with passing querysets to celery tasks
    i.e. pickle serialization. and we would also have to train the users on
    how to configure django celery beat periodic tasks that require arguments.
    thus... let's have separate tasks for each type of report and worry
    about this later
    """
    try:
        return _email_report(
            data=expires_in(),
            subscription_obj=Subscription.objects.get(
                subscription='SSl Report'), logger=LOG)
    except Exception as err:
        raise err


@shared_task(
    queue='ssl', rate_limit='1/s', max_retries=3,
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_ssl_expires_in_days_report(lt_days):  # pylint: disable=invalid-name
    """
    task to send ssl reports about certificates that expire soon via email

    """
    try:
        return _email_report(
            data=expires_in(lt_days=lt_days),
            subscription_obj=Subscription.objects.get(
                subscription='SSl Report'), logger=LOG,
            expires_in_less_than=lt_days)
    except Exception as err:
        raise err


@shared_task(
    queue='ssl', rate_limit='1/s', max_retries=3,
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_expired_ssl_report():
    """
    task to send expired ssl reports via email

    """
    try:
        return _email_report(
            data=has_expired(),
            subscription_obj=Subscription.objects.get(
                subscription='Expired SSl Report'), logger=LOG, expired=True)
    except Exception as err:
        raise err


@shared_task(
    queue='ssl', rate_limit='1/s', max_retries=3,
    retry_backoff=True, autoretry_for=(SMTPConnectError,))
def email_invalid_ssl_report():
    """
    task to send expired ssl reports via email

    """
    try:
        return _email_report(
            data=is_not_yet_valid(),
            subscription_obj=Subscription.objects.get(
                subscription='Invalid SSl Report'), logger=LOG, invalid=True)
    except Exception as err:
        raise err


def _email_report(
        data=None, subscription_obj=None, logger=None, **extra_context):
    try:
        email_report = Email(
            data=data, subscription_obj=subscription_obj, logger=logger,
            **extra_context)
    except Exception as err:
        raise err

    try:
        return email_report.send()
    except Exception as err:
        raise err


@shared_task(task_serializer='pickle', rate_limit='10/s', queue='shared')
def get_ssl_for_node(orion_node):
    """
    initiate an nmap ssl probe task for each known SSL port
    """
    ssl_ports = SslProbePort.objects.filter(enabled=True).all()

    group(get_ssl_for_node_port.
          s(orion_node, ssl_port).
          set(serializer='pickle') for ssl_port in ssl_ports)()

    return 'looking for SSL certificates on Orion node %s (%s), ports %s' % \
        (orion_node.node_caption, orion_node.ip_address,
         ', '.join(str(ssl_ports.values_list('port', flat=True))))


@shared_task(task_serializer='pickle', rate_limit='2/s', queue='nmap',
             autoretry_for=(NmapError, NmapHostDownError),
             max_retries=3, retry_backoff=True)
def get_ssl_for_node_port(orion_node, port):
    """
    get the ssl certificate data for a node and port
    """
    try:
        ssl_certificate = SslProbe(orion_node.ip_address, port)
    except NmapNotAnSslNodeError:
        return 'there is no SSL certificate on {}:{}'.format(
            orion_node.ip_address, port)
    except Exception as error:
        raise error

    LOG.debug('nmap returned %s', ssl_certificate.summary)

    try:
        created, ssl_obj = SslCertificate.create_or_update(
            orion_node.orion_id, ssl_certificate)
    except Exception as error:
        raise error

    if created:
        return 'SSL certificate {} on {}, port {} has been created at {}'.\
            format(ssl_certificate.ssl_subject, ssl_certificate.hostnames,
                   ssl_certificate.port, ssl_obj.created_on)

    return 'SSL certificate {} on {}, port {} last seen at {}'.format(
        ssl_certificate.ssl_subject, ssl_certificate.hostnames,
        ssl_certificate, ssl_obj.last_seen)


@shared_task(rate_limit='2/s', queue='nmap',
             autoretry_for=(NmapError, NmapHostDownError),
             max_retries=3, retry_backoff=True)
def verify_ssl_for_node_port(cert_node_port_tuple):
    """
    for a known node and port do we still have a certificate?
    if not, removw the node_port certificate instance from the database
    """
    port = cert_node_port_tuple[2]
    ip_address = OrionNode.objects.get(
        orion_id=cert_node_port_tuple[1]).ip_address
    try:
        _ = SslProbe(ip_address, port)
    except NmapNotAnSslNodeError:
        SslCertificate.objects.filter(
            id=cert_node_port_tuple[0]).delete()
        return ('there is no SSL certificate on %s:%s.'
                ' removing this certificate from the database' %
                (ip_address, port))

    except Exception as error:
        raise error

    return 'found an SSL certificate on %s:%s.' % (ip_address, port)


@shared_task(queue='shared')
def verify_ssl_certificates():
    """
    verify that the known SSL certificates are still active on their
    respective Orion nodes
    """
    cert_node_port_list = SslCertificate.objects.filter(enabled=True).\
        values_list('id', 'orion_id', 'port__port')

    group(verify_ssl_for_node_port.s(cert_node_port_tuple) for
          cert_node_port_tuple in cert_node_port_list)()

    return 'verifying {} known SSL certificates against Orion nodes'.format(
        len(cert_node_port_list))


@shared_task(queue='shared')
def get_ssl_nodes():
    """
    get the orion nodes and initiate a (set) of ssl probes for each of them
    """
    orion_nodes = OrionSslNode.nodes()
    if not orion_nodes:
        raise OrionDataError(
            'there are no Orion nodes available for SSL nmap probing')

    group(get_ssl_for_node.s(orion_node).set(serializer='pickle') for
          orion_node in orion_nodes)()

    return 'looking for SSL certificates on %s Orion nodes' % len(orion_nodes)
