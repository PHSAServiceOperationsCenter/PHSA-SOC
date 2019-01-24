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

from .db_helper import insert_into_certs_data
from .lib import Email, expires_in, has_expired, is_not_yet_valid
from .models import Subscription, SslProbePort, SslCertificate
from .nmap import (
    SslProbe, NmapError, NmapHostDownError, NmapNotAnSslNodeError,
)
from .utils import process_xml_cert

LOG = get_task_logger(__name__)

SSL_PROBE_OPTIONS = r'-Pn -p 443 --script ssl-cert'


class NmapError(Exception):
    """
    raise on nmap failure
    """
    pass


class NmapXMLError(Exception):
    """
    raise when the XML report from nmap cannot be processed
    """
    pass


class NoSSLCertOnNodeError(Exception):
    """
    raise if there is no SSL certificate on the node probed by nmap
    """
    pass


class SSLDatabaseError(Exception):
    """
    raise if one cannot update the database with the SSL certificate
    collected with nmap
    """
    pass


class OrionDataError(Exception):
    """
    raise when there are no orion nodes available for nmap probing
    """
    pass


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
def email_ssl_expires_in_days_report(lt_days):
    """
    task to send ssl reports about certificates that expire soon via email

    """
    try:
        return _email_report(
            data=expires_in(lt_days),
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
                subscription='Expired SSl Report'), logger=LOG)
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
                subscription='Invalid SSl Report'), logger=LOG)
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


@shared_task(
    rate_limit='0.5/s', queue='nmap', autoretry_for=(NmapError,),
    max_retries=3, retry_backoff=True)
def go_node(node_id, node_address):
    """
    collect SSL certificate data as returned by nmap and save it to the
    database
    """
    try:
        nmap_task = NmapProcess(node_address, options=SSL_PROBE_OPTIONS)
        nmap_task.run()
    except MaxRetriesExceededError as error:
        LOG.error(
            'nmap retry limit exceeded for node address %s', node_address)
        raise error
    except Exception as ex:
        raise NmapError(
            'nmap error for node address %s: %s' % (node_address, str(ex)))

    try:
        json = process_xml_cert(
            node_id, xml.dom.minidom.parseString(nmap_task.stdout))
    except Exception as error:
        LOG.error(
            'cannot process nmap XML report for node address %s: %s',
            node_address, str(error))

    if json["md5"] is None:
        LOG.error(
            'could not retrieve SSL certificate from node address %s'
            % node_address)
        return (
            'could not retrieve SSL certificate from node address %s'
            % node_address)

    try:
        insert_into_certs_data(json)
    except Exception as error:
        raise SSLDatabaseError(
            'cannot insert/update SSL information collected from node'
            ' address %s: %s' % (node_address, str(error)))

    return 'successful SSL nmap probe on node address %s' % node_address


@shared_task(queue='shared')
def getnmapdata():
    """
    get the orion node information that will be used for nmap probes

    #TODO: rename this to get_orion_nodes()
    #TODO: replace the go_node.delay() loop with a celery group
    """
    nodes = OrionSslNode.nodes()
    if not nodes:
        raise OrionDataError(
            'there are no Orion nodes available for SSL nmap probing')

    for node in nodes:
        go_node.delay(node.id, node.ip_address)

    return 'queued SSL nmap probes for %s Orion nodes' % len(nodes)


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
