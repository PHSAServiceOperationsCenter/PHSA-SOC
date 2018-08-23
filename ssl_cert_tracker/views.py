"""
django models for the ssl_certificates app

:module:    ssl_certificates.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

"""

from django.http import HttpResponse


#import ipdb;ipdb.set_trace()

def index(request):
    return HttpResponse('The Call is Success' + str(request))

