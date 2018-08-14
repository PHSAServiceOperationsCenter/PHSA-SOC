"""
.. _admin:

django admin for the orion_integration app

:module:    p_soc_auto.orion_integration.admin

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca
"""
__updated__ = '2018_08_08'

from django.contrib import admin

from .models import OrionNode, OrionNodeCategory, OrionAPMApplication


@admin.register(OrionNode)
class OrionNodeAdmin(admin.ModelAdmin):
    pass


@admin.register(OrionNodeCategory)
class OrionNodeCategoryAdmin(admin.ModelAdmin):
    pass


@admin.register(OrionAPMApplication)
class OrionAPMApplicationAdmin(admin.ModelAdmin):
    pass


# Register your models here.
