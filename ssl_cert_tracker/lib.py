'''
Created on Oct 25, 2018

@author: serban
'''
import collections

from django.db.models import Case, When, CharField, Value, F, Func
from django.db.models.functions import Now
from django.utils import timezone

from templated_email import get_templated_mail


expired = When(not_after__lt=timezone.now(), then=Value('expired'))

not_yet_valid = When(not_before__gt=timezone.now(),
                     then=Value('not yet valid'))

state_field = Case(
    expired, not_yet_valid, default=Value('valid'), output_field=CharField())


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
    from .models import NmapCertsData
    base_queryset = NmapCertsData.objects.filter(enabled=True)

    queryset = base_queryset.\
        annotate(state=state_field).filter(state='valid').\
        annotate(mysql_now=Now()).\
        annotate(expires_in=DateDiff(F('not_after'), F('mysql_now'))).\
        order_by('expires_in')

    return queryset


def has_expired():
    from .models import NmapCertsData
    base_queryset = NmapCertsData.objects.filter(enabled=True)

    queryset = base_queryset.\
        annotate(state=state_field).filter(state='expired').\
        annotate(mysql_now=Now()).\
        annotate(expired=DateDiff(F('mysql_now'), F('not_after'))).\
        order_by('-expired')

    return queryset


def is_not_yet_valid():
    from .models import NmapCertsData
    base_queryset = NmapCertsData.objects.filter(enabled=True)

    queryset = base_queryset.\
        annotate(state=state_field).filter(state='not yet valid').\
        annotate(mysql_now=Now()).\
        annotate(not_yet_valid=DateDiff(F('not_before'), F('mysql_now'))).\
        order_by('-not_yet_valid')

    return queryset


def send_email():
    import ipdb
    ipdb.set_trace()
    headers = ['common_name', 'expires_in', 'not_before', 'not_after']
    data = collections.OrderedDict()
    context = {'report_date_time': timezone.now()}
    context.update(headers=headers)
    context.update(data=list(expires_in().values(*headers)))
    email = get_templated_mail(
        template_name='ssl_cert_valid_email', template_prefix='email/',
        from_email='serban.teodorescu@phsa.ca',
        to=['serban.teodorescu@phsa.ca'], context=context)
    return email


class Email():
    def __init__(self, data=None, subscription_obj=None):
        pass


"""
In [8]: [collections.OrderedDict(value) for value in expires_in().values('common_name','expires_in')]
Out[8]:
[OrderedDict([('common_name', 'spmgmtadm02.phsabc.ehcnet.ca'),
              ('expires_in', 91)]),
 OrderedDict([('common_name', 'spapplsts001.healthbc.org'),
              ('expires_in', 143)]),
 OrderedDict([('common_name', 'spcrnprj001.HealthBC.org'),
              ('expires_in', 194)]),
 OrderedDict([('common_name', 'dev.bcpsls.ca'), ('expires_in', 194)]),
 OrderedDict([('common_name', 'cmsintranet.phsa.ca'), ('expires_in', 194)]),
 OrderedDict([('common_name', 'spappcare010.vch.ca'), ('expires_in', 284)]),
 OrderedDict([('common_name', 'jira.phsa.ca'), ('expires_in', 326)]),
 OrderedDict([('common_name', 'web.bcpsls.ca'), ('expires_in', 432)]),
 OrderedDict([('common_name', 'safets.phsa.ca'), ('expires_in', 538)]),
 OrderedDict([('common_name', 'citrix.phsa.ca'), ('expires_in', 648)]),
 OrderedDict([('common_name', 'internalapps.healthbc.org'),
              ('expires_in', 651)]),
 OrderedDict([('common_name', 'sftp.phsa.ca'), ('expires_in', 687)]),
 OrderedDict([('common_name', 'AH_SPAPPMAV01'), ('expires_in', 10361)])]

In [9]: coco=[collections.OrderedDict(value) for value in expires_in().values('common_name','expires_in')]

In [10]: coco[0].keys()
Out[10]: odict_keys(['common_name', 'expires_in'])

In [11]:

"""
