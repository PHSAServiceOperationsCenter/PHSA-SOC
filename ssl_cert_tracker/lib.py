"""
.. _lib:

library module for the ssl_certificates app

:module:    ssl_certificates.lib

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca

:updated:    Oct. 30, 2018

"""
from django.db.models import Case, When, CharField, Value, F, Func
from django.db.models.functions import Now
from django.utils import timezone

from templated_email import get_templated_mail


expired = When(not_after__lt=timezone.now(), then=Value('expired'))
"""
:var expired: a representation of an SQL WHEN snippet looking for certificates
              that have expired already

:vartype: :class:`<django.db.models.When>`
"""


not_yet_valid = When(not_before__gt=timezone.now(),
                     then=Value('not yet valid'))
"""
:var not_yet_valid: a representation of an SQL WHEN snippet looking for
                    certificates that are not yet valid
                    
:vartype: :class:`<django.db.models.When>`
"""

state_field = Case(
    expired, not_yet_valid, default=Value('valid'), output_field=CharField())
"""
:var state_field: a representation of an SQL CASE snipped that used the
                  WHEN snippetys from above to categorize SSL certificates by
                  their validity state
                  
:vartype: :class:`<django.db.models.Case>`
"""


class DateDiff(Func):
    """
    django wrapper for the MariaDB function DATEDIFF(). see

    `<https://mariadb.com/kb/en/library/datediff/>`_

    need to use the database function to avoid uncaught conversion errors

    the DATEDIFF() function returns for some un-blessed reason a string so we
    need to use a char field which will impose another annotation to
    convert the result to ints for sorting purposes
    """
    function = 'DATEDIFF'
    output_field = CharField()


def expires_in():
    """
    annotation function that prepares a query with calculated values

    the SQL equivalent is something along the lines of
    SELECT DATEDIFF(not_after, NOW()) AS expires_in_x_days FROM table WHERE
    state = 'valid' ORDER BY expires_in_x_days;

    :returns: a django queryset that has access to all the field in
              NmapCertData plus a state field, an expires_in_x_days field, and
              a field with the value returned by the MySql SQL function NOW()
    """
    from .models import NmapCertsData
    base_queryset = NmapCertsData.objects.filter(enabled=True)

    queryset = base_queryset.\
        annotate(state=state_field).filter(state='valid').\
        annotate(mysql_now=Now()).\
        annotate(expires_in_x_days=DateDiff(F('not_after'), F('mysql_now'))).\
        order_by('expires_in_x_days')

    return queryset


def has_expired():
    """
    annotation function that returns data calculated at the database level
    for expired certificates

    :returns: a django queryset
    """
    from .models import NmapCertsData
    base_queryset = NmapCertsData.objects.filter(enabled=True)

    queryset = base_queryset.\
        annotate(state=state_field).filter(state='expired').\
        annotate(mysql_now=Now()).\
        annotate(
            has_expired_x_days_ago=DateDiff(F('mysql_now'), F('not_after'))).\
        order_by('-has_expired_x_days_ago')

    return queryset


def is_not_yet_valid():
    """
    annotation function that returns data calculated at the database level
    for certificates that are not yet valid

    :returns: a django queryset
    """
    from .models import NmapCertsData
    base_queryset = NmapCertsData.objects.filter(enabled=True)

    queryset = base_queryset.\
        annotate(state=state_field).filter(state='not yet valid').\
        annotate(mysql_now=Now()).\
        annotate(
            will_become_valid_in_x_days=DateDiff(F('not_before'),
                                                 F('mysql_now'))).\
        order_by('-will_become_valid_in_x_days')

    return queryset


class NoDataEmailError(Exception):
    """
    raise this if one tries to create an instance of :class:`<Email>` with no
    data
    """
    pass


class NoSubscriptionEmailError(Exception):
    """
    raise this if one tries to create an instance of :class:`<Email>` with no
    subscription object
    """
    pass


class Email():
    """
    a (more or less) subclass of
    :class:`<django.core.mail.EmailMultiAlternatives>` with a body prepared
    from django template

    instances of this class are multi-part (test and html) email messages
    """

    def __init__(self, data=None, subscription_obj=None):
        """
        :arg data: a django queryset
                   the constructor will prepare the template context and pass
                   it to the :function:`<templated_email.get_templated_mail>`
                   which is responsible for rendering the subject and body
                   of the email message

        :arg subscription_obj: an instance of
                               :class:`<ssl_cert_tracker.models.Subscription>`
                               containing all the meta-date required to
                               build and send an email message. this includes
                               template information and pure SMTP data (like
                               email addresses and stuff)
        """
        if data is None:
            raise NoDataEmailError('no data was provided for the email')

        if subscription_obj is None:
            raise NoSubscriptionEmailError(
                'no subscription was provided for the email')

        headers = {
            key: key.replace('_', ' ').title() for key in
            subscription_obj.headers.split(',')
        }

        prepared_data = []
        for data_item in data.values(*headers.keys()):
            prepared_data.append(
                {key: data_item[key] for key in headers.keys()})

        context = dict(report_date_time=timezone.now(),
                       headers=headers,
                       data=prepared_data)
        self.email = get_templated_mail(
            template_name=subscription_obj.template_name,
            template_dir=subscription_obj.template_dir,
            template_prefix=subscription_obj.template_prefix,
            from_email='serbant@gmail.com',
            to=subscription_obj.emails_list.split(','),
            context=context)

    def send(self):
        """
        wrapper around the
        :method:`<django.core.mail.EmailMultiAlternatives.send>`
        """
        return self.email.send()