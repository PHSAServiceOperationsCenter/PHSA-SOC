

"""
.. _utils:

utility  functions for the notification tasks

:module:    p_soc_auto.notification.utils

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca

:update:    Oct. 03 2018

"""

from django.db.models.signals import post_save
from django.dispatch import receiver
from .tasks import send_email_task, send_sms_task

from django.http import HttpResponse, HttpResponseRedirect
from .models import Notification, \
                    Broadcast, \
                    NotificationTypeBroadcast, \
                    NotificationType

from .utils import EmailBroadCast
#from .task import send_email_task


@receiver(post_save, sender=Notification)
def dispatchNotification(sender, instance, created, *args,**kwargs):
    #import ipdb;ipdb.set_trace()
    if created:
        print(instance.pk)
        dispatch_Signals(instance.pk)

    
def dispatch_Signals(pk):
    nObj = Notification(pk=pk)
    noti_type = nObj.notification_type

    ntObj = NotificationType(notification_type = noti_type)

    subscribers = getSubscribers (noti_type)

    ntBroadcast_obj = NotificationTypeBroadcast(notification_type = ntObj.notification_type)
    broadcast_id =  ntBroadcast_obj.broadcast

    broadcast_methods = Broadcast(id = broadcast_id)
    for method in broadcast_methods:
        if method == "email" and subscribers:
            eb = EmailBroadCast(pk, subscribers)
            eb.go()
        else:
            pass
            #PerformOtherwise

def getSubscribers(nType):
    nObj = NotificationType(notification_type = nType)
    print (nObj.subscribers)
    return nObj.subscribers
