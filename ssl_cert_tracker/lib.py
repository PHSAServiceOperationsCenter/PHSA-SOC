"""
.. _ssl_lib:

:ref:`SSL Certificate Tracker Application` Library
--------------------------------------------------

This module contains classes and functions used by other modules in the
application.

:module:    ssl_certificates.lib

:copyright:

    Copyright 2018 - 2019 Provincial Health Service Authority
    of British Columbia

:contact:    daniel.busto@phsa.ca

"""
from enum import Enum
from logging import getLogger
import socket

from django.conf import settings
from django.db.models import (
    Case, When, CharField, BigIntegerField, Value, F, Func, TextField,
)
from django.db.models.functions import Now, Cast, Concat
from django.utils import timezone

from p_soc_auto_base import utils

LOG = getLogger(__name__)
"""
fall-back :class:`logging.Logger` object

If any class or function needs a :class:`logging.Logger` object and if one is
**not** provided by the caller, then this :class:`logging.Logger` object will be
used.
"""


class State(Enum):
    """
    Enumeration class for state control attributes
    """
    VALID = 'valid'
    EXPIRED = 'expired'
    NOT_YET_VALID = 'not yet valid'


CASE_EXPIRED = When(not_after__lt=timezone.now(), then=Value(State.EXPIRED))
"""
a representation of an SQL WHEN snippet using :class:`django.db.models.When`

See `Django Conditional Expressions <https://docs.djangoproject.com/en/2.2/ref/models/conditional-expressions/#conditional-expressions>`__
for detail about :class:`django.db.models.Case` and :class:`django.db.models.When`.

In this particular case, if the value of
:attr:`ssl_cert_tracker.models.SslCertificate.not_after` is less than the current
moment, the `SSL` certificate is expired.
"""


CASE_NOT_YET_VALID = When(not_before__gt=timezone.now(),
                          then=Value(State.NOT_YET_VALID))
"""
a representation of an SQL WHEN snippet using :class:`django.db.models.When`

See `Django Conditional Expressions
<https://docs.djangoproject.com/en/2.2/ref/models/conditional-expressions/#conditional-expressions>`__
for detail about :class:`django.db.models.Case` and :class:`django.db.models.When`.

In this particular case, if the value of
:attr:`ssl_cert_tracker.models.SslCertificate.not_before` is greater than the
current moment, the `SSL` certificate is not yet valid.
"""

STATE_FIELD = Case(
    CASE_EXPIRED, CASE_NOT_YET_VALID, default=Value(State.VALID),
    output_field=CharField())
"""
a representation of an SQL CASE snippet using the SQL WHEN snippets from above

See `Django Conditional Expressions
<https://docs.djangoproject.com/en/2.2/ref/models/conditional-expressions/#conditional-expressions>`__
for detail about :class:`django.db.models.When` and :class:`django.db.models.When`.

In this particular case, we are tracking the `STATE` of the
:class:`ssl_cert_tracker.models.SslCertificate` instance with regards to validity
and expiration dates. The possible cases are:

* :attr:`State.NOT_YET_VALID` (not yet valid)

* :attr:`State.VALID` (the default state)

* :attr:`State.EXPIRED`

"""


class DateDiff(Func):  # pylint: disable=abstract-method
    """
    Subclass of the `Django` :class:`django.db.models.Func` class; used as a
    wrapper for the `MariaDB` `DATEDIFF()
    <https://mariadb.com/kb/en/library/datediff/>`__

    See `Func() expressions
    <https://docs.djangoproject.com/en/2.2/ref/models/expressions/#func-expressions>`__
    in the `Django` docs for more details about wrappers for functions provided
    by the database server.

    We are using the database function for `date` arithmetic in order to avoid
    conversion errors that cannot be caught and handled at the `Django` level.

    For some un-blessed reason, the `DATEDIFF()` function returns  a string.
    If one wants to use the values returned by `DATEDIFF()` for sorting, one
    will have to worry about the sort order between `strings` and `numbers`.
    """
    function = 'DATEDIFF'
    output_field = CharField()


def is_not_trusted(app_label='ssl_cert_tracker', model_name='sslcertificate'):
    """
    :returns:

        a :class:`django.db.models.query.QuerySet` based on the
        :class:`ssl_cert_tracker.models.SslCertificate` filtered on the
        `untrusted` state of each `SSL` certificate in
        the :class:`django.db.models.query.QuerySet`

        The :class:`django.db.models.query.QuerySet` will include a calculated
        field that highlights the `untrusted` state of each `SSL` certificate.

        Observe the  `annotated
        <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
        `alert_body` field used as an argument for the
        :meth:`django.db.models.query.QuerySet.annotate` method of the
        :class:`django.db.models.query.QuerySet`.

    :rtype: :class:`django.db.models.query.QuerySet`

    The arguments for this function have not been hard-coded because we want to
    be able to reuse the function even if :mod:`ssl_cert_tracker.models` changes.

    :arg str app_label:

    :arg str model_name:

    """
    return get_ssl_base_queryset(app_label, model_name).\
        filter(issuer__is_trusted=False).\
        annotate(alert_body=Value('Untrusted SSL Certificate',
                                  output_field=TextField()))


def get_ssl_base_queryset(app_label, model_name, url_annotate=True,
                          issuer_url_annotate=True):
    """
    :returns:

        a :class:`django.db.models.query.QuerySet` based on the
        :class:`ssl_cert_tracker.models.SslCertificate` and `annotated
        <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
        with the absolute path of the `URL` for the
        :class:`Django admin <django.contrib.admin.ModelAdmin>` instance based on
        the related entry in :class:`ssl_cert_tracker.models.SslCertificateIssuer`

        The annotation is present in a field named `url_issuer`.

    This function cannot be abstracted to generate annotations for one or more
    foreign key fields  because the `annotation` names cannot be passed as
    variables

    :arg str app_label:

    :arg str model_name:

    :arg bool url_annotate:

    :arg bool issuer_url_annotate:

    """
    queryset = utils.get_base_queryset(f'{app_label}.{model_name}',
                                       enabled=True)
    if url_annotate:
        queryset = utils.url_annotate(queryset)
    if issuer_url_annotate \
            and app_label in ['ssl_cert_tracker'] \
            and model_name in ['sslcertificate']:
        queryset = queryset.\
            annotate(url_issuer_id=Cast('issuer__id', TextField())).\
            annotate(url_issuer=Concat(
                Value(settings.SERVER_PROTO), Value('://'),
                Value(socket.getfqdn()),
                Value(':'), Value(settings.SERVER_PORT),
                Value('/admin/'),
                Value(app_label), Value('/sslcertificateissuer/'),
                F('url_issuer_id'), Value('/change/'),
                output_field=TextField()))

    return queryset


def expires_in(app_label='ssl_cert_tracker', model_name='sslcertificate',
               lt_days=None):
    """
    :returns:

        a :class:`django.db.models.query.QuerySet` based on the
        :class:`ssl_cert_tracker.models.SslCertificate`

        The :class:`django.db.models.query.QuerySet` returned by this function is:

        * `filtered
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#filter>`__
          to show only the :attr:`State.VALID` `SSL` certificates

        * optionally `filtered
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#filter>`__
          for the interval before the `SSL` certificates will expire

          Note that the parameter for this filter is measured in `days` and
          cannot be smaller than 2.

          If this `filter
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#filter>`__
          is applied, the :class:`django.db.models.query.QuerySet` will be
          `annotated
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
          with the value of the parameter in a field named `expires_in_less_than`,
          and with a field named `alert_body` that contains a corresponding
          alert message

        * `annotated
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
          with the :attr:`STATE_FIELD` in a field named `state`, and a
          :class:`django.db.models.BigIntegerField` field named `expires_in_x_days`

        * ordered ascending on the `expires_in_x_days` field

    :arg str app_label:

    :arg str model_name:

    :arg int lt_days:

        filter by the number of days remaining until the `SSL` certificate
        expires

        If less than 2, set to 2.

    """
    if lt_days and lt_days < 2:
        LOG.warning('expiring in less than 2 days is not supported.'
                    ' resetting lt_days=%s to 2', lt_days)
        lt_days = 2

    queryset = get_ssl_base_queryset(app_label, model_name).\
        annotate(state=STATE_FIELD).filter(state=State.VALID).\
        annotate(mysql_now=Now()).\
        annotate(expires_in=DateDiff(F('not_after'), F('mysql_now'))).\
        annotate(expires_in_x_days=Cast('expires_in', BigIntegerField()))

    if lt_days:
        queryset = queryset.\
            annotate(expires_in_less_than=Value(lt_days, BigIntegerField())).\
            annotate(expires_in_less_than_cast=Cast(
                'expires_in_less_than', CharField())).\
            annotate(alert_body=Concat(
                Value(
                    'SSL Certificate will expire in less than ', TextField()),
                F('expires_in_less_than_cast'),
                Value(' days', TextField()), output_field=TextField())).\
            filter(expires_in_x_days__lt=lt_days)

    queryset = queryset.order_by('expires_in_x_days')

    return queryset


def has_expired(app_label='ssl_cert_tracker', model_name='sslcertificate'):
    """
    :returns:

        a :class:`django.db.models.query.QuerySet` based on the
        :class:`ssl_cert_tracker.models.SslCertificate`

        The :class:`django.db.models.query.QuerySet` returned by this
        function is:

        * `filtered
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#filter>`__
          to show only the :attr:`State.EXPIRED` `SSL` certificates

        * `annotated
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
          with the :attr:`STATE_FIELD` in a field named `state`, and a
          :class:`django.db.models.BigIntegerField` field named
          `has_expired_x_days_ago`

        * ordered descending on the `has_expired_x_days_ago` field

    :arg str app_label:

    :arg str model_name:

    """
    queryset = get_ssl_base_queryset(app_label, model_name).\
        annotate(state=STATE_FIELD).filter(state=State.EXPIRED).\
        annotate(mysql_now=Now()).\
        annotate(has_expired_x_days_ago=DateDiff(F('mysql_now'),
                                                 F('not_after'))).\
        annotate(has_expired_x_days_ago_cast=Cast('has_expired_x_days_ago',
                                                  CharField())).\
        annotate(alert_body=Concat(
            Value('SSL Certificate has expired ', TextField()),
            F('has_expired_x_days_ago_cast'),
            Value(' days ago', TextField()), output_field=TextField())).\
        order_by('-has_expired_x_days_ago')

    return queryset


def is_not_yet_valid(
        app_label='ssl_cert_tracker', model_name='sslcertificate'):
    """
    :returns:

        a :class:`django.db.models.query.QuerySet` based on the
        :class:`ssl_cert_tracker.models.SslCertificate`

        The :class:`django.db.models.query.QuerySet` returned by this function is:

        * `filtered
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#filter>`__
          to show only the :attr:`State.NOT_YET_VALID` `SSL` certificates

        * `annotated
          <https://docs.djangoproject.com/en/2.2/ref/models/querysets/#annotate>`__
          with the :attr:`STATE_FIELD` in a field named `state`, and a
          :class:`django.db.models.BigIntegerField` field named
          'will_become_valid_in_x_days'

        * ordered descending on the 'will_become_valid_in_x_days' field

    :arg str app_label:

    :arg str model_name:

    """
    queryset = get_ssl_base_queryset(app_label, model_name).\
        annotate(state=STATE_FIELD).filter(state=State.NOT_YET_VALID).\
        annotate(mysql_now=Now()).\
        annotate(will_become_valid_in_x_days=DateDiff(
            F('not_before'), F('mysql_now'))).\
        annotate(will_become_valid_in_x_days_cast=Cast(
            'will_become_valid_in_x_days', CharField())).\
        annotate(alert_body=Concat(
            Value('SSL Certificate will become valid in ', TextField()),
            F('will_become_valid_in_x_days_cast'),
            Value(' days', TextField()), output_field=TextField())).\
        order_by('-will_become_valid_in_x_days')

    return queryset


class NoDataEmailError(Exception):
    """
    Custom :exc:`Exception` class

    Raise this exception if one tries to create an instance of :class:`Email`
    with a :attr:`Email.data` attribute of :class:`NoneType` (:attr:`data` is ``None``).

    The expectation is that :attr:`Email.data` is a
    :class:`django.db.models.query.QuerySet` and the :class:`Email` class can handle
    empty `QuerySet` objects. This exception prevents invoking the :class:`Email`
    class without a `data` argument in the constructor.
    """


class NoSubscriptionEmailError(Exception):
    """
    Custom :exc:`Exception` class

    Raise this exception if one tries to create an instance of :class:`Email`
    without specifying the `subscription` key for a :class:`Subscription
    <ssl_cert_tracker.models.Subscription>` instance.
    """
