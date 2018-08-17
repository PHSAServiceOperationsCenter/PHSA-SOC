from django.shortcuts import render
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.views.generic.edit import FormView
from django.shortcuts import redirect
from datetime import datetime
import time

from .new_tasks import getnmapdata

from .models import MyCertsData

#import ipdb;ipdb.set_trace()

def index(request):
    return HttpResponse('The Call is Success')

def nMapData(request):
    return HttpResponse('The Call is Success')

def certsData(request):
    return HttpResponse('under review')

def certsData(request):
    return HttpResponse('The Call is Success')
