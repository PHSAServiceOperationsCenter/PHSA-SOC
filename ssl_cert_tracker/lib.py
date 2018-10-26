'''
Created on Oct 25, 2018

@author: serban
'''
from django.db.models import (
    Case, When, CharField, Value, F, Func, CharField, Now)
from django.utils import timezone

from .models import NmapCertsData

base_queryset = NmapCertsData.objects.filter(enabled=True)

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
    queryset = base_queryset.\
        annotate(state=state_field).filter(state='valid').\
        annotate(mysql_now=Now()).\
        annotate(expires_in=DateDiff(F('not_after'), F('mysql_now'))).\
        order_by('-expires_in')

    return queryset


def has_expired():
    queryset = base_queryset.\
        annotate(state=state_field).filter(state='expired').\
        annotate(mysql_now=Now()).\
        annotate(expired=DateDiff(F('mysql_now'), F('not_after'))).\
        order_by('-expired')

    return queryset


def is_not_yet_valid():
    queryset = base_queryset.\
        annotate(state=state_field).filter(state='not yet valid').\
        annotate(mysql_now=Now()).\
        annotate(not_yet_valid=DateDiff(F('not_before'), F('mysql_now'))).\
        order_by('-not_yet_valid')

    return queryset
