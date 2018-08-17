#!/usr/bin/env python
from random import choice
from celery import Celery
from celery import shared_task, task
from celery.decorators import periodic_task
from libnmap.process import NmapProcess
import sys
import logging
import datetime
from datetime import datetime
from datetime import date
from pocApp.models import MyCertsData
from rules.models import MyCertsRule

from pocApp.serializers import MyCertsDataSerializer
from rules.serializers import MyCertsRuleSerializer
logger = logging.Logger('catch_all')

from pyknow import *

class MyFact(Fact):
    """Info about the traffic light."""
    pass


class CertificateRule(KnowledgeEngine):
    @Rule(MyFact()) # This is the LHS
    def match_with_every_myfact(self):
        pass

    @DefFacts()
    def needed_data(self):
        record = MyCertsData.objects.filter(status__exact='new')
        if not record:
            return ""
        serilizer = MyCertsDataSerializer(record, many=True)
        notAfter = serilizer.data[0]['valid_end']
        format_str = '%Y-%m-%d'
        curr_date = str(date.today()) 
        d1 = datetime.strptime(notAfter, "%Y-%m-%d")
        d2 = datetime.strptime(curr_date, "%Y-%m-%d")
        diff = abs((d1 - d2).days)
        print (d1, d2, diff)
        if diff <= 7:
            yield Fact("week", color_code="red")
        elif diff <= 14:
            yield Fact("fortnight", color_code="orange")
        elif diff <= 30:
            yield Fact("month", color_code="yellow")
        elif diff <= 90:
            yield Fact("threemonth", color_code="yellow-green")
        else:
            yield Fact("threemonthplus", color_code="green")


    @Rule(Fact("week", color_code="red"))
    def match_with_week(self):
        print("week Rule Response Here")

    @Rule(Fact("fortnight", color_code="orange"))
    def match_with_fortnight(self):
        print("fortnight Rule Response Here")

    @Rule(Fact("month", color_code="yellow"))
    def match_with_month(self):
        print("month Rule Response Here")

    @Rule(Fact("threemonth", color_code="yellow-green"))
    def match_with_threemonth(self):
        print("threemonth Rule Response Here")

    @Rule(Fact("threemonthplus", color_code="green"))
    def match_with_threemonthplus(self):
        print("threemonth plus Rule Response Here") 

#def myPyknow():
#    engine = CertificateRule()
#    engine.reset()
#    engine.declare(MyFact())
#    engine.run()

#if __name__ == '__main__':
#   myPyknow()

@shared_task
def certrules():
    engine = CertificateRule()
    engine.reset()
    engine.declare(MyFact())
    engine.run()
