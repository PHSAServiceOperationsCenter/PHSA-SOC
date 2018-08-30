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

from .models import (
    OrionNode, OrionNodeCategory, OrionAPMApplication, OrionCSTNode,
)


@admin.register(OrionCSTNode)
class OrionCSTNodeAdmin(admin.ModelAdmin):
    """
    admin intrface for the OrionCSTNode model
    """
    pass


@admin.register(OrionNode)
class OrionNodeAdmin(admin.ModelAdmin):
    """
    admin interface for the OrionNode model
    """
    pass


@admin.register(OrionNodeCategory)
class OrionNodeCategoryAdmin(admin.ModelAdmin):
    """
    admin interface for the OrionNodeCategory model
    """
    pass


@admin.register(OrionAPMApplication)
class OrionAPMApplicationAdmin(admin.ModelAdmin):
    """
    admin interface for the OrionAPApplication model
    """
    pass
