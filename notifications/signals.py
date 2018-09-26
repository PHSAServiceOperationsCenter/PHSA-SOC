
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
#from .tasks import send_email, send_sms
from django.core.mail import send_mail
from django.conf import settings


@receiver(post_save, sender=Notification)
def dispatch(sender, instance, created, **kwargs):
    print ("Mark I")
    print ("self.parameter_list")
    subject = "self.message['rule']"
    message = "self.message['object_field']"
    email_from = settings.EMAIL_HOST_USER
    recipient_list = ['phsadev@gmail.com',]
    send_mail( subject, message, email_from, recipient_list )


