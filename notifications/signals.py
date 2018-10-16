
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notification
from .tasks import send_email_task, send_sms_task


@receiver(post_save, sender=Notification)
def dispatch(sender, instance, created, **kwargs):
    pass
    # send_email_task.delay(Notification.pk)
