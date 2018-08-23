from django.db import models
from django.forms import ModelForm
from django.urls import reverse
from datetime import date
from django.utils import timezone

from django.contrib.auth.models import AbstractUser
from django.core.validators import MaxValueValidator, MinValueValidator


class MyCertsRule(models.Model):
    recid = models.AutoField(primary_key=True)
    intervals= models.CharField(max_length=100, blank=True, null=True)
    code = models.CharField(max_length=100, blank=True, null=True)

