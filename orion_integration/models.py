"""
.. _models:

django models for the orion_integration app

:module:    p_soc_auto.orion_integration.models

:copyright:

    Copyright 2018 Provincial Health Service Authority
    of British Columbia

:contact:    serban.teodorescu@phsa.ca
"""
__updated__ = '2018_08_08'

from django.conf import settings
from django.db import IntegrityError, models
from django.utils.translation import gettext_lazy as _

from p_soc_auto_base.models import BaseModel

from .orion import OrionClient


class OrionQueryError(Exception):
    """
    raise if the model doesn't have an orion_query attribute
    """
    pass


class OrionMappingsError(Exception):
    """
    raise if the model doesn't have an orion_mappings attribute
    """
    pass


class OrionBaseModel(BaseModel, models.Model):
    """
    most (if not all) Orion objects need an orion_id key that comes from the
    Orion server

    then we also need the fields from the BaseModel; let's use this as the
    base class for all the models here
    """
    orion_query = None
    orion_mappings = None

    orion_id = models.BigIntegerField(
        _('Orion Object Id'), db_index=True, unique=True, blank=False,
        help_text=_(
            'Use the value in this field to query the Orion server'))

    @classmethod
    def update_or_create_from_orion(cls):
        """
        class method to update or create orion model instances

        update or create entries in orion models using data from the Orion
        server

        :arg cls: the model class

            note that this method is defined in a base class so that it can
            be invoked from all the classes inheriting form that particular
            base class
        """
        if cls.orion_query is None:
            raise OrionQueryError(
                _('%s is not providing a value for the Orion query'
                  % cls._meta.label))

        if cls.orion_mappings is None:
            raise OrionMappingsError(
                _('%s is not providing a value for the Orion mappings'
                  % cls._meta.label))

        user = cls.get_or_create_user(settings.ORION_USER)
        data = OrionClient.populate_from_query(cls)
        for data_item in data:
            orion_mapping = dict()
            for mapping in cls.orion_mappings:
                orion_mapping[mapping[0]] = data_item[mapping[1]]

            orion_mapping.update(update_by=user)
            try:
                cls.objects.update_or_create(**orion_mapping)
            except IntegrityError:
                orion_mapping.update(created_by=user)
                cls.objects.update_or_create(**orion_mapping)

    class Meta:
        abstract = True


class OrionNodeStatus(OrionBaseModel, models.Model):
    """
    """
    status = models.CharField(
        _('Node Status'), max_length=254, db_index=True, unique=True,
        blank=False, null=False)

    class Meta:
        app_label = 'orion_integration'
        verbose_name = 'Orion Node Status'
        verbose_name_plural = 'Orion Node Statuses'


class OrionNode(OrionBaseModel, models.Model):
    """
    reference:
    `Orion Node<http://solarwinds.github.io/OrionSDK/schema/Orion.Nodes.html>`_

    query:
    SELECT IPAddress, Caption, NodeDescription, Description, DNS, 
    Category, Vendor, Location, Status, MachineType,  NodeName, DetailsUrl
    FROM Orion.Nodes WHERE Category = (Category.category=server)
    we will have to change this if we ever start worrying about routers and
    stuff

    """
    node_caption = models.CharField(
        _('Node Caption'), db_index=True, unique=True, blank=False,
        max_length=254, null=False)
    category = models.ForeignKey(
        'OrionNodeCategory', on_delete=models.PROTECT,
        verbose_name=_('Orion Node Category'))
    ip_address = models.GenericIPAddressField(
        _('IP Address'), db_index=True, unique=True, blank=False, null=False,
        protocol='IPv4')
    node_name = models.CharField(
        _('Node Name'), db_index=True, blank=False, null=False, max_length=254)
    node_dns = models.CharField(
        _('DNS'), db_index=True, blank=False, null=False, max_length=254)
    node_description = models.TextField(_('Orion Node Description'))
    vendor = models.CharField(
        _('Vendor'), db_index=True, blank=True, null=True, max_length=254)
    location = models.CharField(
        _('Location'), db_index=True, blank=True, null=True, max_length=254)
    machine_type = models.CharField(
        _('Machine Type'), db_index=True, blank=True, null=True,
        max_length=254, help_text=_('this needs to become a foreign key'))
    status = models.ForeignKey('OrionNodeStatus', on_delete=models.PROTECT)


class OrionNodeCategory(OrionBaseModel, models.Model):
    """
    query:
    SELECT Description FROM Orion.NodeCategories
    """
    orion_query = 'SELECT CategoryID, Description FROM Orion.NodeCategories'
    orion_mappings = (('orion_id', 'CategoryID'),
                      ('category', 'Description'))
    category = models.CharField(
        _('Orion Node Category'), db_index=True, unique=True, null=False,
        blank=False, max_length=254, help_text=_(
            'Orion Node Category Help'))

    class Meta:
        app_label = 'orion_integration'
        verbose_name = _('Orion Node Category')
        verbose_name_plural = _('Orion Node Categories')
