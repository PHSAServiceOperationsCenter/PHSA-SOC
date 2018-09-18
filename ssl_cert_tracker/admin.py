"""
.. _admin:

django admin for the orion_integration app

:module:    p_soc_auto.ssl_cert_tracker.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    ali.rahmat@phsa.ca
"""
__updated__ = '2018_08_08'


from django.contrib import admin
from .models import NmapCertsData


@admin.register(NmapCertsData)
class NmapCertsDataAdmin(admin.ModelAdmin):
    """NmapCertsDataAdmin to be displayed on admin page  """
    pass


@admin.register(NmapHistory)
class NmapHistoryAdmin(admin.ModelAdmin):
    """NmapHistoryAdmin to be displayed on admin page  """
    pass

