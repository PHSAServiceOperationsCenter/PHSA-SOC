# Register your models here
from django.contrib import admin

from .models import NmapCertsData


@admin.register(NmapCertsData)
class NmapCertsDataAdmin(admin.ModelAdmin):
    pass
